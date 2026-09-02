"""
Technical Analysis Service
--------------------------
Calculates institutional support & resistance levels and Point of Control (POC):
- Swing high/low pivot identification
- Zone clustering within +/- 1%
- 4 Golden Rules scoring (Touch count, Role Reversal, Volume Confirmation, Round Numbers)
- Robust Volume Profile Point of Control (POC) with 3-Layer Outlier Resistance:
  1. Winsorization (Caps 1-day volume spikes at 3.5x 20d SMA)
  2. 5-Slice Intra-day Candle Distribution (Between High and Low)
  3. TPO Time Weighting (Volume weighted by sqrt of unique session count)
"""

import math
import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, Any, Optional
from scipy.signal import argrelextrema

from strategies.base_strategy import download_stock_history


class TechnicalAnalysisService:
    @staticmethod
    def calculate_support_resistance(stock: str, current_price: float = None) -> dict:
        """
        Identifies key Support and Resistance levels and computes the Robust Volume POC.
        """
        empty = {
            "supports": [],
            "resistances": [],
            "distanceToSupport1Pct": None,
            "distanceToResistance1Pct": None,
            "poc": None
        }
        try:
            df = download_stock_history(stock, lookback_years=1, min_bars=30)
            if df is None or df.empty:
                return empty

            closes = df["Close"].values.astype(float)
            highs = df["High"].values.astype(float)
            lows = df["Low"].values.astype(float)
            volumes = df["Volume"].values.astype(float)

            price_now = float(current_price) if current_price else float(closes[-1])

            # 1. Swing Highs & Lows (Order=5)
            order = 5
            swing_low_idx = argrelextrema(lows, np.less_equal, order=order)[0]
            swing_high_idx = argrelextrema(highs, np.greater_equal, order=order)[0]

            vol_20d_avg = pd.Series(volumes).rolling(20, min_periods=5).mean().values

            def build_candidate(idx_arr, price_arr, side):
                candidates = []
                for i in idx_arr:
                    p = float(price_arr[i])
                    if math.isnan(p) or math.isinf(p) or p <= 0:
                        continue
                    v_avg = vol_20d_avg[i] if i < len(vol_20d_avg) else 0
                    vol_ratio = (volumes[i] / v_avg) if (v_avg and v_avg > 0 and not math.isnan(v_avg)) else 1.0
                    candidates.append({
                        "price": p,
                        "bar_index": int(i),
                        "volume_ratio": float(vol_ratio),
                        "side": side,
                    })
                return candidates

            raw_supports = build_candidate(swing_low_idx, lows, "support")
            raw_resistances = build_candidate(swing_high_idx, highs, "resistance")

            # 2. Cluster levels within +/-1%
            def cluster_levels(candidates):
                if not candidates:
                    return []
                sorted_c = sorted(candidates, key=lambda x: x["price"])
                clusters = []
                current_cluster = [sorted_c[0]]
                for c in sorted_c[1:]:
                    ref = current_cluster[0]["price"]
                    if abs(c["price"] - ref) / ref <= 0.01:
                        current_cluster.append(c)
                    else:
                        clusters.append(current_cluster)
                        current_cluster = [c]
                clusters.append(current_cluster)

                merged = []
                for cluster in clusters:
                    avg_price = np.mean([c["price"] for c in cluster])
                    max_vol_ratio = max(c["volume_ratio"] for c in cluster)
                    touch_count = len(cluster)
                    merged.append({
                        "price": round(float(avg_price), 2),
                        "touchCount": touch_count,
                        "volumeRatio": round(max_vol_ratio, 2),
                        "barIndices": [c["bar_index"] for c in cluster],
                        "side": cluster[0]["side"],
                    })
                return merged

            support_zones = cluster_levels(raw_supports)
            resistance_zones = cluster_levels(raw_resistances)

            # 3. Round number detection (+/-0.5%)
            def near_round_number(price):
                if price is None:
                    return False
                try:
                    p_val = float(price)
                    if math.isnan(p_val) or math.isinf(p_val) or p_val <= 0:
                        return False
                    magnitudes = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 1500, 2000, 5000]
                    for mag in magnitudes:
                        nearest = round(p_val / mag) * mag
                        if nearest > 0 and abs(p_val - nearest) / nearest <= 0.005:
                            return True
                except Exception:
                    pass
                return False

            # 4. Role reversal detection
            all_resistance_prices = {z["price"] for z in resistance_zones}
            all_support_prices = {z["price"] for z in support_zones}

            def is_role_reversal(price, side):
                threshold = 0.015
                if side == "support":
                    return any(abs(price - r) / r <= threshold for r in all_resistance_prices if r > price * 0.98)
                else:
                    return any(abs(price - s) / s <= threshold for s in all_support_prices if s < price * 1.02)

            # 5. Score each zone (4 Golden Rules)
            def score_zone(zone):
                score = 0
                reasons = []

                if zone["touchCount"] >= 3:
                    score += 2
                    reasons.append(f"touched {zone['touchCount']}×")
                elif zone["touchCount"] == 2:
                    score += 1
                    reasons.append(f"touched {zone['touchCount']}×")

                if is_role_reversal(zone["price"], zone["side"]):
                    score += 2
                    reasons.append("role reversal")

                if zone["volumeRatio"] >= 1.5:
                    score += 1
                    reasons.append(f"vol {zone['volumeRatio']:.1f}×")

                if near_round_number(zone["price"]):
                    score += 1
                    reasons.append("round number")

                zone["strength"] = score
                zone["reasons"] = reasons
                zone["roundNumber"] = near_round_number(zone["price"])
                zone["volumeConfirmed"] = zone["volumeRatio"] >= 1.5
                zone["roleReversal"] = is_role_reversal(zone["price"], zone["side"])
                return zone

            support_zones = [score_zone(z) for z in support_zones]
            resistance_zones = [score_zone(z) for z in resistance_zones]

            # 6. Filter relative to CMP, sort by strength
            support_zones = sorted(
                [z for z in support_zones if z["price"] < price_now],
                key=lambda x: (-x["strength"], -(price_now - x["price"]) / price_now)
            )[:4]

            resistance_zones = sorted(
                [z for z in resistance_zones if z["price"] > price_now],
                key=lambda x: (-x["strength"], -(x["price"] - price_now) / price_now)
            )[:4]

            # 7. Robust Volume Profile POC (Point of Control)
            poc_price = None
            poc_side = None
            try:
                price_min = float(lows.min())
                price_max = float(highs.max())
                num_bins = 100
                bin_edges = np.linspace(price_min, price_max, num_bins + 1)

                safe_vol_sma = np.nan_to_num(vol_20d_avg, nan=float(np.mean(volumes)))
                capped_volumes = np.minimum(volumes, safe_vol_sma * 3.5)

                mid_prices = (highs + lows) / 2.0
                bin_indices = np.digitize(mid_prices, bin_edges) - 1
                bin_sessions = np.zeros(num_bins)
                for b in bin_indices:
                    bin_sessions[min(b, num_bins - 1)] += 1

                adj_bin_volumes = np.zeros(num_bins)
                for i in range(len(capped_volumes)):
                    v_day = capped_volumes[i]
                    slices = np.linspace(lows[i], highs[i], 5)
                    slice_bins = np.digitize(slices, bin_edges) - 1
                    for sb in slice_bins:
                        adj_bin_volumes[min(sb, num_bins - 1)] += v_day / 5.0

                composite_scores = adj_bin_volumes * np.sqrt(np.maximum(bin_sessions, 1))
                poc_bin = int(np.argmax(composite_scores))
                poc_price = round(float((bin_edges[poc_bin] + bin_edges[poc_bin + 1]) / 2.0), 2)
                poc_side = "support" if poc_price < price_now else "resistance"
            except Exception:
                pass

            def pct_distance(level, ref):
                return round((level - ref) / ref * 100, 2)

            def clean_zone(z):
                return {k: v for k, v in z.items() if k not in ("barIndices", "volumeRatio")}

            supports_clean = [clean_zone(z) for z in support_zones]
            resistances_clean = [clean_zone(z) for z in resistance_zones]

            dist_s1 = pct_distance(support_zones[0]["price"], price_now) if support_zones else None
            dist_r1 = pct_distance(resistance_zones[0]["price"], price_now) if resistance_zones else None

            poc_zone = None
            if poc_price is not None:
                poc_zone = {
                    "price": poc_price,
                    "side": poc_side,
                    "touchCount": "—",
                    "strength": 6,
                    "reasons": ["volume POC", "highest traded volume"],
                    "roundNumber": near_round_number(poc_price),
                    "volumeConfirmed": True,
                    "roleReversal": False,
                    "isPOC": True,
                }

            return {
                "supports": supports_clean,
                "resistances": resistances_clean,
                "distanceToSupport1Pct": dist_s1,
                "distanceToResistance1Pct": dist_r1,
                "poc": poc_zone,
            }

        except Exception as e:
            print(f"Error computing S/R for {stock}: {e}")
            return empty
