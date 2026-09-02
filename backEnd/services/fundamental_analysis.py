"""
Fundamental Analysis Service
----------------------------
Handles scraping and parsing of company fundamentals from Screener.in & yfinance:
- Key valuation ratios (P/E, Market Cap, Debt to Equity, ROCE, ROE)
- Historical Median P/E calculation (1Y, 3Y, 5Y) via Screener Chart API
- Quarterly EPS history for 4 trailing quarters
- Shareholding pattern (Promoter, FII, DII, Public) and QoQ changes
- 4-Point Health Rating Scorecard calculation
"""

import re
import math
import requests
import urllib.parse
import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import financialMath


class FundamentalAnalysisService:
    @staticmethod
    def fetch_from_screener(stock: str, session: requests.Session, headers: dict) -> dict:
        """
        Scrapes key ratios, quarterly results, and shareholding pattern from Screener.in.
        """
        urls = [
            f"https://www.screener.in/company/{stock}/consolidated/",
            f"https://www.screener.in/company/{stock}/"
        ]
        
        soup = None
        matched_url = None
        for url in urls:
            try:
                resp = session.get(url, headers=headers, timeout=6)
                if resp.status_code == 200 and "Company not found" not in resp.text:
                    soup = BeautifulSoup(resp.content, "html.parser")
                    matched_url = url
                    break
            except Exception:
                continue

        if not soup:
            return {}

        data = {}
        if matched_url:
            data["_isConsolidated"] = "consolidated" in matched_url

        try:
            # Extract Exact Company ID from page attribute
            comp_tag = soup.find(attrs={"data-company-id": True})
            if comp_tag:
                data["_companyId"] = comp_tag["data-company-id"]

            # Company Name
            h1 = soup.find("h1", class_="h2") or soup.find("h1")
            if h1:
                data["companyName"] = h1.get_text(strip=True)

            # Top Ratios (P/E, Market Cap, Debt to Equity, ROCE, ROE)
            top_ratios = soup.find("ul", id="top-ratios")
            if top_ratios:
                for item in top_ratios.find_all("li"):
                    name_span = item.find("span", class_="name")
                    val_span = item.find("span", class_="value") or item.find("span", class_="nowrap")
                    if name_span and val_span:
                        name = name_span.get_text(strip=True).lower()
                        val_txt = val_span.get_text(strip=True).replace(",", "")
                        
                        num_match = re.search(r"[-+]?\d*\.?\d+", val_txt)
                        num_val = float(num_match.group()) if num_match else None

                        if "stock p/e" in name or name == "p/e":
                            data["peRatio"] = num_val
                        elif "debt to equity" in name:
                            data["debtToEquity"] = num_val
                        elif "current price" in name:
                            data["currentPrice"] = num_val
                        elif "market cap" in name:
                            data["marketCap"] = num_val
                        elif "roce" in name:
                            data["roce"] = num_val
                        elif "roe" in name:
                            data["roe"] = num_val

            # Quarterly EPS
            quarterly_sec = soup.find("section", id="quarters")
            if quarterly_sec:
                table = quarterly_sec.find("table", class_="data-table")
                if table:
                    headers_list = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]
                    quarter_names = headers_list[1:] if len(headers_list) > 1 else []
                    
                    eps_row = None
                    for tr in table.find("tbody").find_all("tr"):
                        tds = tr.find_all("td")
                        if tds and "eps in rs" in tds[0].get_text(strip=True).lower():
                            eps_row = [td.get_text(strip=True).replace(",", "") for td in tds[1:]]
                            break

                    if eps_row and quarter_names:
                        quarterly_eps = []
                        for q_name, eps_str in zip(quarter_names, eps_row):
                            try:
                                val = float(eps_str)
                                quarterly_eps.append({"quarter": q_name, "eps": val})
                            except ValueError:
                                continue
                        
                        last_4 = quarterly_eps[-4:] if len(quarterly_eps) >= 4 else quarterly_eps
                        data["quarterlyEps"] = last_4
                        data["epsLast4Qtrs"] = [item["eps"] for item in last_4]

            # Shareholding Pattern
            shareholding_sec = soup.find("section", id="shareholding")
            if shareholding_sec:
                table = shareholding_sec.find("table", class_="data-table")
                if table:
                    for tr in table.find("tbody").find_all("tr"):
                        tds = tr.find_all("td")
                        if len(tds) >= 3:
                            holder_name = tds[0].get_text(strip=True).lower()
                            
                            def parse_pct(txt):
                                clean = txt.replace("%", "").replace(",", "").strip()
                                try:
                                    return float(clean)
                                except ValueError:
                                    return 0.0

                            all_vals = [parse_pct(td.get_text(strip=True)) for td in tds[1:]]
                            latest_val = all_vals[-1] if all_vals else 0.0
                            prev_val = all_vals[-2] if len(all_vals) >= 2 else latest_val
                            diff = round(latest_val - prev_val, 2)
                            
                            if "promoter" in holder_name:
                                data["promoterHolding"] = latest_val
                                data["promoterChange"] = diff
                                data["promoterHistory"] = all_vals[-4:]
                            elif "fii" in holder_name:
                                data["fiiHolding"] = latest_val
                                data["fiiChange"] = diff
                                data["fiiHistory"] = all_vals[-4:]
                            elif "dii" in holder_name:
                                data["diiHolding"] = latest_val
                                data["diiChange"] = diff
                                data["diiHistory"] = all_vals[-4:]
                            elif "public" in holder_name:
                                data["publicHolding"] = latest_val
                                data["publicHistory"] = all_vals[-4:]

        except Exception as e:
            print(f"Error parsing screener data for {stock}: {e}")

        return data

    @staticmethod
    def fetch_from_yfinance(stock: str) -> dict:
        """
        Fetches PE, D/E, market prices, and calculates 14-period RSI using yfinance.
        """
        data = {}
        for suffix in [".NS", ".BO"]:
            ticker_symbol = f"{stock}{suffix}"
            try:
                ticker = yf.Ticker(ticker_symbol)
                info = ticker.info
                if info and isinstance(info, dict):
                    if not data.get("peRatio"):
                        data["peRatio"] = info.get("trailingPE") or info.get("forwardPE")
                        if data["peRatio"]:
                            data["peRatio"] = round(float(data["peRatio"]), 2)
                            
                    if not data.get("debtToEquity"):
                        de = info.get("debtToEquity")
                        if de is not None:
                            data["debtToEquity"] = round(float(de) / 100.0, 2) if float(de) > 5.0 else round(float(de), 2)
                            
                    if not data.get("currentPrice"):
                        data["currentPrice"] = info.get("currentPrice") or info.get("regularMarketPrice")
                    if not data.get("marketCap"):
                        data["marketCap"] = info.get("marketCap")
                        
                hist = ticker.history(period="3mo")
                if hist is not None and not hist.empty and len(hist) >= 15:
                    closes = hist["Close"].tolist()
                    rsi_val = financialMath.calculate_rsi(closes, period=14)
                    if rsi_val is not None:
                        data["rsi"] = rsi_val

                if data.get("peRatio") or data.get("rsi"):
                    break
            except Exception:
                continue

        return data

    @staticmethod
    def fetch_historical_pe_medians(
        stock: str, 
        session: requests.Session,
        headers: dict,
        current_pe: float = None, 
        company_id: int = None, 
        is_consolidated: bool = True
    ) -> dict:
        """
        Fetches 1Y, 3Y, and 5Y Median PE values from Screener's chart API.
        """
        result = {
            "peMedian1Y": None,
            "peMedian3Y": None,
            "peMedian5Y": None,
            "belowMedian1Y": None,
            "belowMedian3Y": None,
            "belowMedian5Y": None,
        }
        try:
            if not company_id:
                search_url = f"https://www.screener.in/api/company/search/?q={urllib.parse.quote(stock)}"
                search_resp = session.get(search_url, headers=headers, timeout=6)
                if search_resp.status_code == 200:
                    search_data = search_resp.json()
                    if search_data:
                        matched = None
                        for item in search_data:
                            url_parts = [p for p in item.get("url", "").split("/") if p and p != "company" and p != "consolidated"]
                            if url_parts and url_parts[0].upper() == stock.upper():
                                matched = item
                                break

                        if not matched:
                            for item in search_data:
                                name_words = item.get("name", "").upper().split()
                                if name_words and name_words[0] == stock.upper():
                                    matched = item
                                    break

                        if not matched:
                            matched = search_data[0]

                        company_id = matched.get("id")
                        if "consolidated" in matched.get("url", ""):
                            is_consolidated = True

            if not company_id:
                return result

            q_param = urllib.parse.quote("Price to Earning-Median PE-EPS")
            medians = {}
            current_pe_from_chart = None

            for days, key in [(365, "1Y"), (1095, "3Y"), (1825, "5Y")]:
                responses_to_try = []
                if is_consolidated:
                    responses_to_try.append(f"https://www.screener.in/api/company/{company_id}/chart/?q={q_param}&days={days}&consolidated=true")
                responses_to_try.append(f"https://www.screener.in/api/company/{company_id}/chart/?q={q_param}&days={days}")

                for chart_url in responses_to_try:
                    try:
                        chart_resp = session.get(chart_url, headers={
                            **headers,
                            "X-Requested-With": "XMLHttpRequest",
                            "Accept": "application/json, */*",
                            "Referer": f"https://www.screener.in/company/{stock}/",
                        }, timeout=6)

                        if chart_resp.status_code != 200:
                            continue

                        chart_data = chart_resp.json()
                        datasets = chart_data.get("datasets", [])
                        if not datasets:
                            continue

                        for ds in datasets:
                            metric = ds.get("metric", "").lower()
                            label = ds.get("label", "").lower()
                            values = ds.get("values", [])

                            if "median" in metric or "median" in label:
                                if values:
                                    try:
                                        medians[key] = round(float(values[0][1]), 2)
                                    except (ValueError, TypeError, IndexError):
                                        pass

                            if current_pe_from_chart is None and "price to earning" in metric and values:
                                try:
                                    current_pe_from_chart = round(float(values[-1][1]), 2)
                                except (ValueError, TypeError, IndexError):
                                    pass

                        if key in medians:
                            break
                    except Exception:
                        continue

            result["peMedian1Y"] = medians.get("1Y")
            result["peMedian3Y"] = medians.get("3Y")
            result["peMedian5Y"] = medians.get("5Y")

            compare_pe = current_pe if current_pe is not None else current_pe_from_chart
            if compare_pe is not None:
                result["belowMedian1Y"] = bool(compare_pe < medians["1Y"]) if medians.get("1Y") is not None else None
                result["belowMedian3Y"] = bool(compare_pe < medians["3Y"]) if medians.get("3Y") is not None else None
                result["belowMedian5Y"] = bool(compare_pe < medians["5Y"]) if medians.get("5Y") is not None else None

        except Exception as e:
            print(f"Error fetching PE medians from Screener for {stock}: {e}")

        return result

    @staticmethod
    def calculate_stock_rating(data: dict) -> dict:
        """
        Computes the 4-check Health Rating scorecard (0 to 4).
        """
        checks = {}
        
        # Check 1: FII holding peak
        fii_hist = data.get("fiiHistory", [])
        if len(fii_hist) >= 2:
            last3 = fii_hist[-3:] if len(fii_hist) >= 3 else fii_hist
            latest_fii = last3[-1]
            prior_fii = last3[:-1]
            fii_passed = latest_fii >= (max(prior_fii) - 0.02)
            detail_str = f"Current: {latest_fii:.2f}% vs Prior [{', '.join(f'{v:.2f}%' for v in prior_fii)}]"
        else:
            fii_change = data.get("fiiChange")
            fii_passed = fii_change is not None and fii_change >= -0.02
            detail_str = f"QoQ: {fii_change:+.2f}%" if fii_change is not None else "No history"

        checks["fiiHolding"] = {
            "title": "FII Peak Accumulation",
            "rule": "Current quarter FII holding is the highest vs last 2 quarters",
            "passed": bool(fii_passed),
            "detail": detail_str
        }

        # Check 2: P/E vs Medians
        pe = data.get("peRatio")
        m1 = data.get("peMedian1Y")
        m3 = data.get("peMedian3Y")
        m5 = data.get("peMedian5Y")
        medians_available = [m for m in [m1, m3, m5] if m is not None]
        
        if pe is not None and medians_available:
            pe_passed = all(pe < m for m in medians_available)
            pe_details = f"P/E {pe:.1f}x vs 1Y: {m1 or '—'}x, 3Y: {m3 or '—'}x, 5Y: {m5 or '—'}x"
        else:
            pe_passed = False
            pe_details = "Median PE data unavailable"

        checks["peValuation"] = {
            "title": "Valuation vs Historical Medians",
            "rule": "Current P/E < 1Y, 3Y, and 5Y Median P/E",
            "passed": bool(pe_passed),
            "detail": pe_details
        }

        # Check 3: RSI <= 55
        rsi = data.get("rsi")
        if rsi is not None and rsi > 0:
            rsi_passed = rsi <= 55.0
            rsi_detail = f"RSI: {rsi:.1f} (≤ 55)" if rsi_passed else f"RSI: {rsi:.1f} (> 55)"
        else:
            rsi_passed = False
            rsi_detail = "RSI data unavailable"

        checks["rsiMomentum"] = {
            "title": "Momentum Entry Zone",
            "rule": "14-day RSI under 55 (not overbought)",
            "passed": bool(rsi_passed),
            "detail": rsi_detail
        }

        # Check 4: Consistent QoQ Earnings Trend
        eps_list = data.get("epsLast4Qtrs", [])
        if len(eps_list) >= 2:
            total_steps = len(eps_list) - 1
            growth_steps = sum(1 for i in range(1, len(eps_list)) if eps_list[i] >= eps_list[i-1] - 0.02)
            min_required = max(1, int(round(total_steps * 0.65)))
            eps_passed = (growth_steps >= min_required) and (eps_list[-1] >= eps_list[0] - 0.02)
            trend_str = " → ".join(f"₹{v:.1f}" for v in eps_list)
            eps_detail = f"[{trend_str}] ({growth_steps}/{total_steps} QoQ steps)"
        else:
            eps_passed = False
            eps_detail = "Quarterly EPS history unavailable"

        checks["epsGrowth"] = {
            "title": "Consistent Earnings Growth",
            "rule": "Sequential QoQ growth across at least 3 of last 4 quarters",
            "passed": bool(eps_passed),
            "detail": eps_detail
        }

        score = sum(1 for c in checks.values() if c["passed"])
        return {
            "ratingScore": score,
            "maxScore": 4,
            "ratingChecks": checks
        }
