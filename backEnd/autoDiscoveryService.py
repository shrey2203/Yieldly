"""
Automatic Investment Discovery & 5-Year Data Backfill Service
-------------------------------------------------------------
Automatically discovers newly added Equities and Mutual Funds from user trade files,
inserts them into EQUITY_MASTER / MF_MASTER, and backfills 5 years of historical
market data (or all available data since inception if newer).
No manual SQL insert queries needed!
"""

import os
import re
import time
import requests
import difflib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any

from config import db
from dataQuery.equityMasterQuery import EquityMaster
from dataQuery.equityMarketDataQuery import EquityMarketData
from dataQuery.mutualFundMasterQuery import MutualFundMaster
from dataQuery.mutualFundMarketDataQuery import MutualFundMarketData
import state

HOLDINGS_DIR = '/Users/bhavya/Downloads/HOLDINGS'

# Known ticker renames / aliases on NSE/BSE
EQUITY_ALIASES = {
    'ZEE': 'ZEEL',
    'BERGERPAINT': 'BERGEPAINT',
    'TRENT': 'TRENT',
    'TATAMOTOR': 'TATAMOTORS'
}


def auto_discover_equity(symbol: str) -> Optional[EquityMaster]:
    """
    Check if equity exists in EQUITY_MASTER. If not, lookup on Yahoo Finance,
    create EQUITY_MASTER record, and backfill 5-year historical market data.
    """
    if not symbol:
        return None
    sym = str(symbol).strip().upper()
    if sym in ['TOTAL', 'EQUITY', 'SUM']:
        return None

    # Check if already in DB
    existing = EquityMaster.query.filter_by(equityShortName=sym).first()
    if existing:
        return existing

    print(f"[AutoDiscovery] New equity detected: '{sym}'. Discovering on Yahoo Finance...")

    # Determine yfinance ticker symbol
    lookup_sym = EQUITY_ALIASES.get(sym, sym)
    ticker_candidates = [
        f"{lookup_sym}.NS",
        f"{lookup_sym}.BO",
        lookup_sym
    ]

    import yfinance as yf
    ticker = None
    hist = None
    active_ticker_symbol = None

    for cand in ticker_candidates:
        try:
            t = yf.Ticker(cand)
            # Try 5-year daily history (or all available if newer)
            h = t.history(period="5y", interval="1d")
            if h is not None and len(h) > 0:
                ticker = t
                hist = h
                active_ticker_symbol = cand
                break
        except Exception as e:
            print(f"[AutoDiscovery] Candidate {cand} failed: {e}")

    # Extract metadata
    long_name = sym
    sector = "Other"
    y_high = 0
    y_low = 0

    if ticker:
        try:
            info = ticker.info or {}
            long_name = info.get("longName") or info.get("shortName") or sym
            sector = info.get("sector") or info.get("industry") or "Other"
            y_high = int(float(info.get("fiftyTwoWeekHigh") or 0))
            y_low = int(float(info.get("fiftyTwoWeekLow") or 0))
        except Exception:
            pass

    # Create new EquityMaster record
    new_equity = EquityMaster(
        equityShortName=sym,
        equityLongName=long_name,
        yearHigh=y_high,
        yearLow=y_low,
        sector=sector,
        lastUpdatedTime=datetime.now(),
        divLastUpdatedTime=datetime.now()
    )
    db.session.add(new_equity)
    db.session.flush()

    eq_id = new_equity.getId()

    # Populate 5-year historical OHLC data
    rows_added = 0
    if hist is not None and len(hist) > 0:
        market_data_objects = []
        for idx, row in hist.iterrows():
            m_date = idx.date()
            o_val = float(row.get("Open", 0))
            c_val = float(row.get("Close", 0))
            l_val = float(row.get("Low", 0))
            h_val = float(row.get("High", 0))

            market_data_objects.append(
                EquityMarketData(
                    equityId=eq_id,
                    marketDate=m_date,
                    open=o_val,
                    close=c_val,
                    low=l_val,
                    high=h_val
                )
            )
        db.session.bulk_save_objects(market_data_objects)
        rows_added = len(market_data_objects)

    db.session.commit()
    state.equityMasterCache[eq_id] = new_equity
    print(f"[AutoDiscovery] Successfully registered equity '{sym}' (ID: {eq_id}) with {rows_added} historical days!")
    return new_equity


_CACHED_SCHEMES = None

def _get_all_mf_schemes():
    global _CACHED_SCHEMES
    if _CACHED_SCHEMES is None:
        try:
            res = requests.get("https://api.mfapi.in/mf", timeout=15)
            if res.status_code == 200:
                _CACHED_SCHEMES = res.json()
        except Exception as e:
            print(f"[AutoDiscovery] Error fetching mfapi.in schemes list: {e}")
            _CACHED_SCHEMES = []
    return _CACHED_SCHEMES or []


def find_best_mf_match(fund_name: str) -> Optional[Dict[str, Any]]:
    """
    Intelligently find the matching scheme code from mfapi.in for a given fund name.
    """
    all_schemes = _get_all_mf_schemes()
    if not all_schemes:
        return None

    fn = fund_name.lower().strip()
    # Normalize AMC
    tokens = fn.split()
    amc = tokens[0] if tokens else ""
    if amc in ['aditya', 'birla']: amc = 'aditya'
    elif amc in ['icici', 'pru']: amc = 'icici'
    elif amc in ['parag', 'ppfas']: amc = 'parag'
    elif amc in ['motilal']: amc = 'motilal'

    is_direct = bool(re.search(r'\b(dir|direct)\b', fn))
    is_regular = bool(re.search(r'\b(reg|regular)\b', fn)) or (not is_direct)
    is_growth = bool(re.search(r'\(g\)|growth', fn))

    clean = re.sub(r'\s*\([^)]*\)', '', fn)
    clean = re.sub(r'\b(reg|regular|dir|direct|fund|plan|sl|pru)\b', '', clean).strip()
    words = [w for w in re.split(r'[\s\-&]+', clean) if len(w) > 2]

    candidates = []
    for s in all_schemes:
        sname = s['schemeName'].lower()
        if amc and amc not in sname:
            continue
        # plan type
        if is_growth and 'growth' not in sname:
            continue
        if is_direct and 'direct' not in sname:
            continue
        if is_regular and 'direct' in sname:
            continue

        ratio = difflib.SequenceMatcher(None, clean, sname).ratio()
        w_match = sum(1 for w in words if w in sname)
        score = w_match * 10 + ratio * 5
        candidates.append((score, s))

    if candidates:
        candidates.sort(key=lambda x: -x[0])
        return candidates[0][1]

    # Fallback to direct mfapi search API if in-memory search yielded nothing
    try:
        q_words = [w for w in clean.split() if len(w) > 2][:3]
        query = " ".join(q_words)
        res = requests.get(f"https://api.mfapi.in/mf/search?q={requests.utils.quote(query)}", timeout=10)
        if res.status_code == 200:
            results = res.json()
            if results:
                return results[0]
    except Exception:
        pass

    return None


def auto_discover_mutual_fund(fund_name: str) -> Optional[MutualFundMaster]:
    """
    Check if mutual fund exists in MF_MASTER. If not, discover schemeCode,
    create MF_MASTER record, and backfill 5-year historical daily NAVs.
    """
    if not fund_name:
        return None
    fn = str(fund_name).strip()

    existing = MutualFundMaster.query.filter_by(mutualFund=fn).first()
    if existing:
        return existing

    print(f"[AutoDiscovery] New Mutual Fund detected: '{fn}'. Searching schemeCode...")
    match = find_best_mf_match(fn)
    if not match:
        print(f"[AutoDiscovery] Could not automatically match scheme code for '{fn}'.")
        return None

    scheme_code = str(match['schemeCode'])
    scheme_name = match.get('schemeName', fn)
    print(f"[AutoDiscovery] Matched '{fn}' to scheme code {scheme_code} ({scheme_name})")

    new_mf = MutualFundMaster(
        mutualFund=fn,
        ISIN=scheme_code,
        lastUpdatedTime=datetime.now(),
        dayWisePositionlastUpdatedTime=datetime.now()
    )
    db.session.add(new_mf)
    db.session.flush()

    mf_id = new_mf.getId()

    # Fetch 5-year NAV history from mfapi.in
    cutoff_date = (datetime.now() - timedelta(days=5 * 365.25)).date()
    rows_added = 0
    try:
        url = f"https://api.mfapi.in/mf/{scheme_code}"
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            data = res.json().get('data', [])
            nav_objects = []
            for item in data:
                try:
                    d = datetime.strptime(item['date'], "%d-%m-%Y").date()
                    if d < cutoff_date:
                        continue
                    nav_val = float(item['nav'])
                    nav_objects.append(
                        MutualFundMarketData(
                            mutualFundId=mf_id,
                            marketDate=d,
                            nav=nav_val
                        )
                    )
                except Exception:
                    continue
            if nav_objects:
                db.session.bulk_save_objects(nav_objects)
                rows_added = len(nav_objects)
    except Exception as e:
        print(f"[AutoDiscovery] Error fetching historical NAVs for {scheme_code}: {e}")

    db.session.commit()
    state.mutualFundMasterCache[mf_id] = new_mf
    print(f"[AutoDiscovery] Successfully registered MF '{fn}' (Code: {scheme_code}) with {rows_added} NAV records!")
    return new_mf


def auto_sync_all_investments():
    """
    Scans all Excel files in HOLDINGS_DIR and automatically registers
    any missing equities or mutual funds with 5-year history.
    """
    if not os.path.exists(HOLDINGS_DIR):
        return

    print("[AutoDiscovery] Scanning HOLDINGS directory for new investments...")

    # 1. Scan Equities
    excel_equities = set()
    for fname in os.listdir(HOLDINGS_DIR):
        if fname.endswith('.xlsx') and not fname.endswith('_MF.xlsx') and not fname.startswith('~$') and fname != 'COMBINED.xlsx':
            try:
                df = pd.read_excel(os.path.join(HOLDINGS_DIR, fname))
                eq_col = next((col for col in df.columns if str(col).strip().upper() in ['EQUITY', 'STOCK', 'SYMBOL']), None)
                if eq_col:
                    for s in df[eq_col].dropna().unique():
                        s_clean = str(s).strip().upper()
                        if s_clean and s_clean not in ['TOTAL', 'EQUITY', 'SUM']:
                            excel_equities.add(s_clean)
            except Exception as e:
                print(f"[AutoDiscovery] Error reading equity file {fname}: {e}")

    existing_equities = {e.getEquityShortName().strip().upper() for e in EquityMaster.query.all()}
    missing_equities = excel_equities - existing_equities
    if missing_equities:
        print(f"[AutoDiscovery] Found {len(missing_equities)} new equities: {missing_equities}")
        for sym in missing_equities:
            auto_discover_equity(sym)

    # 2. Scan Mutual Funds
    excel_mfs = set()
    for fname in os.listdir(HOLDINGS_DIR):
        if fname.endswith('_MF.xlsx') and not fname.startswith('~$') and fname != 'COMBINED_MF.xlsx':
            try:
                df = pd.read_excel(os.path.join(HOLDINGS_DIR, fname))
                col = df.columns[1] if len(df.columns) > 1 else None
                if col:
                    for f in df[col].dropna().unique():
                        f_clean = str(f).strip()
                        if f_clean:
                            excel_mfs.add(f_clean)
            except Exception as e:
                print(f"[AutoDiscovery] Error reading MF file {fname}: {e}")

    existing_mfs = {m.getMutualFund().strip() for m in MutualFundMaster.query.all()}
    missing_mfs = excel_mfs - existing_mfs
    if missing_mfs:
        print(f"[AutoDiscovery] Found {len(missing_mfs)} new mutual funds: {missing_mfs}")
        for mf_name in missing_mfs:
            auto_discover_mutual_fund(mf_name)

    # 3. Synchronize Combined positions as exact sum of all users
    backfill_combined_positions()


def sync_all_users_equity_positions():
    """
    Ensures Shrey, Monica, Yogesh, and Bhavya are fully up-to-date
    in Equity_DayWisePosition up to latestMarketDate before Combined is aggregated.
    """
    import helperFunctions
    import fetchEquityDayWisePnlPosition
    import initialiseApplication
    import state
    
    if not state.equityMasterCache:
        initialiseApplication.initiateCacheEquity()
        
    latest_market_date = helperFunctions.getLatestExistingEquityMarketData()
    if not latest_market_date:
        return
        
    for username in ['SHREY', 'MONICA', 'YOGESH', 'BHAVYA']:
        uid = helperFunctions.getUserId(username.lower())
        if not uid:
            continue
        user_latest = helperFunctions.getLatestDateForDayWiseEquityPosition(uid)
        if user_latest is None or user_latest < latest_market_date:
            try:
                df = helperFunctions.getUserEquityDataFrame(username)
                fetchEquityDayWisePnlPosition.persistEquityDayWisePnlPosition(username, df)
                print(f"[AutoDiscovery] Synced equity positions for {username} up to {latest_market_date}")
            except Exception as e:
                print(f"[AutoDiscovery] Error syncing equity positions for {username}: {e}")


def backfill_combined_positions():
    """
    Deletes position data for Combined (userId=1) and re-aggregates it
    as the exact sum of all individual user positions (Shrey 2, Monica 3, Yogesh 4, Bhavya 5).
    """
    from sqlalchemy import text
    import state
    
    # 0. Ensure all individual accounts are up-to-date
    sync_all_users_equity_positions()
    
    print("[AutoDiscovery] Synchronizing Combined (userId=1) positions as sum of Shrey, Monica, Yogesh, Bhavya...")
    
    # 1. Delete existing Combined position data
    db.session.execute(text('DELETE FROM Equity_DayWisePosition WHERE userId = 1'))
    db.session.execute(text('DELETE FROM MF_DayWisePosition WHERE userId = 1'))
    
    # 2. Backfill Equity_DayWisePosition
    db.session.execute(text('''
        INSERT INTO Equity_DayWisePosition (
            userId, equityId, asOfDate, totalInvestment, currentInvestment, quantity, avgPrice, dailyChange
        )
        SELECT 
            1 AS userId,
            equityId,
            asOfDate,
            ROUND(SUM(totalInvestment), 2) AS totalInvestment,
            ROUND(SUM(currentInvestment), 2) AS currentInvestment,
            ROUND(SUM(quantity), 4) AS quantity,
            CASE 
                WHEN SUM(quantity) > 0 THEN ROUND(SUM(totalInvestment) / SUM(quantity), 2)
                ELSE 0 
            END AS avgPrice,
            ROUND(SUM(dailyChange), 2) AS dailyChange
        FROM Equity_DayWisePosition
        WHERE userId IN (2, 3, 4, 5)
        GROUP BY equityId, asOfDate
        HAVING (SUM(quantity) != 0 OR SUM(totalInvestment) != 0 OR SUM(currentInvestment) != 0)
    '''))
    
    # 3. Backfill MF_DayWisePosition
    db.session.execute(text('''
        INSERT INTO MF_DayWisePosition (
            userId, mutualFundId, asOfDate, totalInvestment, currentInvestment
        )
        SELECT 
            1 AS userId,
            mutualFundId,
            asOfDate,
            ROUND(SUM(totalInvestment), 2) AS totalInvestment,
            ROUND(SUM(currentInvestment), 2) AS currentInvestment
        FROM MF_DayWisePosition
        WHERE userId IN (2, 3, 4, 5)
        GROUP BY mutualFundId, asOfDate
        HAVING (SUM(totalInvestment) != 0 OR SUM(currentInvestment) != 0)
    '''))
    
    db.session.commit()
    if hasattr(state, 'dashboardOverviewCache'):
        state.dashboardOverviewCache.clear()
    if hasattr(state, 'portfolioResponseCache'):
        state.portfolioResponseCache.clear()
    print("[AutoDiscovery] Combined position data successfully backfilled and synchronized!")

