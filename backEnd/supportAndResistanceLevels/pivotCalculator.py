import os
import sys
import numpy as np
import pandas as pd
from sqlalchemy import desc

# Handle directory hierarchy so imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your existing DB context and models
from config import app
from dataQuery.equityMarketDataQuery import EquityMarketData

class OhlcRejectionAnalysis:
    """
    Identifies support and resistance zones based on price clustering 
    and OHLC rejection confirmations.
    """
    def __init__(self, records):
        data = [{
            'High': float(r.high),
            'Low': float(r.low),
            'Close': float(r.close),
            'Date': r.marketDate
        } for r in records]
        self.df = pd.DataFrame(data)
        
    def find_rejection_zones(self, price_type, delta_pct=0.015, min_rejections=2, zone_width_pct=0.03):
        """
        :param zone_width_pct: Total width of the returned zone (default 0.03 = 3%)
        """
        prices = np.sort(self.df[price_type].dropna().values)
        if len(prices) == 0: 
            return []
        
        clusters = []
        current_cluster = [prices[0]]
        
        for price in prices[1:]:
            margin = current_cluster[-1] * delta_pct
            if abs(price - current_cluster[-1]) <= margin:
                current_cluster.append(price)
            else:
                clusters.append(current_cluster)
                current_cluster = [price]
        clusters.append(current_cluster)
        
        valid_zones = []
        
        for cluster in clusters:
            if len(cluster) >= min_rejections:
                cluster_mean = np.mean(cluster)
                margin = cluster_mean * delta_pct
                
                if price_type == 'High':
                    rejections = self.df[
                        (self.df['High'] >= (cluster_mean - margin)) & 
                        (self.df['Close'] < cluster_mean)
                    ]
                else:
                    rejections = self.df[
                        (self.df['Low'] <= (cluster_mean + margin)) & 
                        (self.df['Close'] > cluster_mean)
                    ]
                    
                if len(rejections) >= min_rejections:
                    # Create a percentage-based band around the center (e.g., +/- 1.5% for a 3% zone)
                    half_band = zone_width_pct / 2
                    
                    valid_zones.append({
                        'center': round(cluster_mean, 2),
                        'range_bottom': round(cluster_mean * (1 - half_band), 2),
                        'range_top': round(cluster_mean * (1 + half_band), 2),
                        'strength': len(rejections)
                    })
                    
        return sorted(valid_zones, key=lambda x: x['strength'], reverse=True)


def get_support_resistance(equity_id, lookback=1200, delta_pct=0.015, min_rejections=2, zone_width_pct=0.03):
    """Fetches data and calculates S/R levels."""
    with app.app_context():
        records = EquityMarketData.query.filter_by(equityId=equity_id)\
                                       .order_by(desc(EquityMarketData.marketDate))\
                                       .limit(lookback)\
                                       .all()
        
        if not records: 
            return None
        
        analyzer = OhlcRejectionAnalysis(records)
        resistances = analyzer.find_rejection_zones('High', delta_pct=delta_pct, min_rejections=min_rejections, zone_width_pct=zone_width_pct)
        supports = analyzer.find_rejection_zones('Low', delta_pct=delta_pct, min_rejections=min_rejections, zone_width_pct=zone_width_pct)
        
        return {
            "lookback_days": len(records),
            "zone_width": f"{zone_width_pct * 100}%",
            "resistance_zones": resistances,
            "support_zones": supports
        }


if __name__ == "__main__":
    print("--- OHLC Support & Resistance Analyzer ---")
    
    try:
        user_input = input("Enter Equity ID to analyze: ")
        target_equity_id = int(user_input.strip())
    except ValueError:
        print("Invalid input. Please enter a numeric Equity ID.")
        sys.exit(1)

    print(f"\nFetching data for Equity ID: {target_equity_id}...")
    
    # 3% zone configuration is passed dynamically here
    result = get_support_resistance(target_equity_id, zone_width_pct=0.03)
    
    if not result:
        print(f"FAILED: No market data found for equity ID {target_equity_id}")
    else:
        print(f"Data Analyzed: Last {result['lookback_days']} trading days")
        print(f"Band Width: {result['zone_width']} (+/- {float(result['zone_width'].strip('%')) / 2}% from center)")
        
        print("\n--- RESISTANCE ZONES (Ceilings) ---")
        if not result['resistance_zones']:
            print("None found meeting the criteria.")
        for r in result['resistance_zones']:
            print(f"Zone: {r['range_bottom']:>8.2f} to {r['range_top']:<8.2f} (Center: {r['center']:.2f})  |  Strength (Rejections): {r['strength']}")
            
        print("\n--- SUPPORT ZONES (Floors) ---")
        if not result['support_zones']:
            print("None found meeting the criteria.")
        for s in result['support_zones']:
            print(f"Zone: {s['range_bottom']:>8.2f} to {s['range_top']:<8.2f} (Center: {s['center']:.2f})  |  Strength (Rejections): {s['strength']}")
        print("\n")