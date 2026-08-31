import os
import pandas as pd
from datetime import datetime, timedelta
from config import db
from sqlalchemy import desc

from dataQuery.userQuery import User
from dataQuery.equityMasterQuery import EquityMaster
from dataQuery.equityMarketDataQuery import EquityMarketData
from dataQuery.equityDayWisePositionQuery import EquityDayWisePosition

HOLDINGS_DIR = '/Users/bhavya/Downloads/HOLDINGS'

def getUserId(username):
    if not username:
        return None
    allUsersQueried = User.query.all()
    for user in allUsersQueried:
        if str(username).lower() == user.getUserName().lower(): 
            return user.getId()
            
    # If username is 'combined' and not in DB, auto-create it
    if str(username).lower() == "combined":
        try:
            combined_user = User(username="COMBINED", panNumber="COMBINED_ALL", emailAddress="combined@yieldly.com")
            db.session.add(combined_user)
            db.session.commit()
            return combined_user.getId()
        except Exception as e:
            db.session.rollback()
            existing = User.query.filter(User.username.ilike("combined")).first()
            if existing:
                return existing.getId()
    return None


def getUserEquityDataFrame(username):
    """
    Fetch equity holdings DataFrame for a specific user,
    or dynamically aggregate all non-combined user holdings for 'COMBINED'.
    """
    uname = str(username or '').strip().upper()
    if uname == 'COMBINED':
        dfs = []
        all_users = User.query.filter(User.username != 'COMBINED').all()
        user_names = [u.getUserName().upper() for u in all_users] if all_users else []
        if not user_names and os.path.exists(HOLDINGS_DIR):
            for fname in os.listdir(HOLDINGS_DIR):
                if fname.endswith('.xlsx') and not fname.endswith('_MF.xlsx') and not fname.startswith('~$') and fname != 'COMBINED.xlsx':
                    user_names.append(os.path.splitext(fname)[0].upper())
                    
        for u in set(user_names):
            fpath = os.path.join(HOLDINGS_DIR, f"{u}.xlsx")
            if os.path.exists(fpath):
                try:
                    df = pd.read_excel(fpath, 0)
                    df['ACCOUNT'] = u
                    dfs.append(df)
                except Exception as e:
                    print(f"Error reading equity holdings for {u}: {e}")
                    
        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            date_col = next((c for c in combined.columns if str(c).strip().upper() == 'DATE'), 'DATE')
            if date_col in combined.columns:
                combined[date_col] = pd.to_datetime(combined[date_col])
                combined = combined.sort_values(by=date_col).reset_index(drop=True)
            return combined
            
        combined_file = os.path.join(HOLDINGS_DIR, "COMBINED.xlsx")
        if os.path.exists(combined_file):
            return pd.read_excel(combined_file, 0)
        raise FileNotFoundError("No equity holdings files found for combined portfolio.")
    else:
        excelPath = os.path.join(HOLDINGS_DIR, f"{uname}.xlsx")
        return pd.read_excel(excelPath, 0)


def getUserMutualFundDataFrame(username):
    """
    Fetch mutual fund holdings DataFrame for a specific user,
    or dynamically aggregate all non-combined user transactions for 'COMBINED'.
    """
    uname = str(username or '').strip().upper()
    if uname == 'COMBINED':
        dfs = []
        all_users = User.query.filter(User.username != 'COMBINED').all()
        user_names = [u.getUserName().upper() for u in all_users] if all_users else []
        if not user_names and os.path.exists(HOLDINGS_DIR):
            for fname in os.listdir(HOLDINGS_DIR):
                if fname.endswith('_MF.xlsx') and not fname.startswith('~$') and fname != 'COMBINED_MF.xlsx':
                    user_names.append(fname.replace('_MF.xlsx', '').upper())
                    
        for u in set(user_names):
            fpath = os.path.join(HOLDINGS_DIR, f"{u}_MF.xlsx")
            if os.path.exists(fpath):
                try:
                    df = pd.read_excel(fpath, 0)
                    df['ACCOUNT'] = u
                    dfs.append(df)
                except Exception as e:
                    print(f"Error reading MF holdings for {u}: {e}")
                    
        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            if len(combined.columns) > 0:
                combined[combined.columns[0]] = pd.to_datetime(combined[combined.columns[0]])
                combined = combined.sort_values(by=combined.columns[0]).reset_index(drop=True)
            return combined
            
        combined_file = os.path.join(HOLDINGS_DIR, "COMBINED_MF.xlsx")
        if os.path.exists(combined_file):
            return pd.read_excel(combined_file, 0)
        raise FileNotFoundError("No MF holdings files found for combined portfolio.")
    else:
        excel_file = os.path.join(HOLDINGS_DIR, f"{uname}_MF.xlsx")
        return pd.read_excel(excel_file, 0)

        
def getLatestExistingEquityMarketData():
    latestMarketData = EquityMarketData.query.order_by(desc(EquityMarketData.marketDate)).first()
    return latestMarketData.getMarketDate()


def getLatestDateForDayWiseEquityPosition(userId):
    latestDate = EquityDayWisePosition.query.filter_by(userId = userId).order_by(desc(EquityDayWisePosition.asOfDate)).first()
    if latestDate:
        return latestDate.getAsOfDate()
    return datetime(2018,1,1).date()