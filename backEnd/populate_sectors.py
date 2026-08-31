"""
Script to populate missing/empty sectors for all stocks in EQUITY_MASTER database.
Uses yfinance (NSE .NS / BSE .BO) with rate-limiting, retry fallbacks, and batch commits.

Usage:
    cd backEnd
    python populate_sectors.py
    
Optional Arguments:
    python populate_sectors.py --force       # Overwrite existing sectors as well
    python populate_sectors.py --dry-run     # Preview without saving to DB
"""

import sys
import time
import argparse
import yfinance as yf
from datetime import datetime

# Setup Flask application context
from config import app, db
from dataQuery.equityMasterQuery import EquityMaster

# Fallback mapping for common ETFs, REITs, Indices, and Indian Scrips
FALLBACK_SECTOR_MAP = {
    # Index ETFs / Gold / Silver
    "NIFTYBEES": "ETFs & Indices",
    "BANKBEES": "Financial Services (ETF)",
    "GOLDBEES": "Commodities & Precious Metals",
    "SILVERBEES": "Commodities & Precious Metals",
    "JUNIORBEES": "ETFs & Indices",
    "ITBEES": "Technology (ETF)",
    "PHARMABEES": "Healthcare (ETF)",
    "AUTOBEES": "Consumer Cyclical (ETF)",
    "PSUBNKBEES": "Financial Services (ETF)",
    "CPSEETF": "ETFs & Indices",
    "MON100": "International ETFs",
    "MAFANG": "International ETFs",
    # REITs & InvITs
    "EMBASSY": "Real Estate (REIT)",
    "MINDSPACE": "Real Estate (REIT)",
    "BROOKFIELD": "Real Estate (REIT)",
    "NEXUS": "Real Estate (REIT)",
    "PGINVIT": "Utilities & Infrastructure (InvIT)",
    "IRBINVIT": "Utilities & Infrastructure (InvIT)",
}

def clean_symbol(symbol: str) -> str:
    """Sanitize stock symbol for Yahoo Finance query."""
    sym = symbol.strip().upper()
    # Replace & with %26 or clean format if applicable
    sym = sym.replace('&', '_').replace(' ', '')
    return sym

def fetch_sector_info(symbol: str):
    """
    Fetch sector and industry for a stock symbol.
    Attempts NSE (.NS) first, then BSE (.BO).
    """
    cleaned = clean_symbol(symbol)
    
    # Check fallback map first
    if cleaned in FALLBACK_SECTOR_MAP:
        return FALLBACK_SECTOR_MAP[cleaned], "ETF / REIT / Trust"
        
    for suffix in [".NS", ".BO"]:
        ticker_symbol = f"{cleaned}{suffix}"
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            if info and isinstance(info, dict):
                sector = info.get("sector")
                industry = info.get("industry")
                
                # Check if valid sector returned
                if sector and sector.strip() and sector.strip().lower() not in ["", "other", "none", "unknown"]:
                    return sector.strip(), industry.strip() if industry else "General"
                
                # If sector is missing but quoteType is ETF/MUTUALFUND
                quote_type = info.get("quoteType", "")
                if quote_type == "ETF":
                    return "ETFs & Funds", "Exchange Traded Fund"
        except Exception as e:
            # Silently continue to try next exchange suffix
            continue

    return None, None


def populate_sectors(force_all=False, dry_run=False):
    """
    Scan EQUITY_MASTER records and populate missing sectors.
    """
    with app.app_context():
        equities = EquityMaster.query.all()
        total_count = len(equities)
        print("=" * 70)
        print(f"🚀 EQUITY SECTOR POPULATOR — Total Records in DB: {total_count}")
        print(f"⚙️  Settings: Force All = {force_all} | Dry Run = {dry_run}")
        print("=" * 70)

        # Filter candidates for update
        candidates = []
        for eq in equities:
            current_sector = (eq.getSector() or "").strip()
            if force_all or not current_sector or current_sector.lower() in ["", "other", "unknown", "none"]:
                candidates.append(eq)

        candidates_count = len(candidates)
        print(f"📊 Target Equities to process: {candidates_count} / {total_count}\n")

        if candidates_count == 0:
            print("✅ All equities already have valid sector classifications! Nothing to do.")
            return

        updated_count = 0
        skipped_count = 0
        failed_count = 0

        start_time = datetime.now()

        for idx, equity in enumerate(candidates, start=1):
            short_name = equity.getEquityShortName()
            current_sector = (equity.getSector() or "").strip()
            progress = f"[{idx}/{candidates_count}] ({idx/candidates_count*100:.1f}%)"

            # Fetch sector via yfinance
            sector, industry = fetch_sector_info(short_name)

            if sector:
                if not dry_run:
                    equity.sector = sector
                    equity.lastUpdatedTime = datetime.utcnow()
                    
                print(f"{progress} ✅ {short_name:<18} ➔ {sector} ({industry})")
                updated_count += 1
            else:
                print(f"{progress} ⚠️  {short_name:<18} ➔ Could not detect sector (Left as '{current_sector or 'Other'}')")
                if not current_sector and not dry_run:
                    equity.sector = "Other"
                failed_count += 1

            # Commit in batches of 10 for safety
            if not dry_run and idx % 10 == 0:
                db.session.commit()

            # Small sleep to be polite to yfinance API rate limits
            time.sleep(0.3)

        if not dry_run:
            db.session.commit()

        elapsed = (datetime.now() - start_time).total_seconds()

        print("\n" + "=" * 70)
        print(f"🎉 EXECUTION FINISHED in {elapsed:.1f}s")
        print(f"   • Updated: {updated_count}")
        print(f"   • Unresolved / Fallback: {failed_count}")
        print(f"   • Total Processed: {candidates_count}")
        print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate Sector classifications in EQUITY_MASTER SQLite table.")
    parser.add_argument("--force", action="store_true", help="Re-fetch and overwrite sectors for all stocks (even if already populated).")
    parser.add_argument("--dry-run", action="store_true", help="Simulate fetching sectors without writing changes to the SQLite database.")
    args = parser.parse_args()

    populate_sectors(force_all=args.force, dry_run=args.dry_run)
