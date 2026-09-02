import os
import pandas as pd
from datetime import datetime, timedelta
from config import db
from sqlalchemy import desc, func

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
    if str(username).lower() == 'combined':
        newUser = User(username='Combined', panNumber='COMBINED', emailAddress='combined@yieldly.com')
        db.session.add(newUser)
        db.session.commit()
        return newUser.getId()
    return None

def getCombinedUsers():
    all_users = User.query.filter(func.lower(User.username) != 'combined').all()
    user_names = [u.getUserName().upper() for u in all_users if u.getUserName().upper() != 'COMBINED']
    if not user_names and os.path.exists(HOLDINGS_DIR):
        for fname in os.listdir(HOLDINGS_DIR):
            if fname.endswith('.xlsx') and not fname.endswith('_MF.xlsx') and not fname.startswith('~$'):
                clean_name = os.path.splitext(fname)[0].upper()
                if clean_name != 'COMBINED':
                    user_names.append(clean_name)
    return [u for u in set(user_names) if u != 'COMBINED']

def getUserEquityDataFrame(username):
    """
    Fetch equity holdings DataFrame for a specific user,
    or dynamically aggregate all individual user holdings (excluding COMBINED.xlsx).
    """
    uname = str(username or '').strip().upper()
    if uname == 'COMBINED':
        dfs = []
        user_names = getCombinedUsers()
                    
        for u in user_names:
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
            
        raise FileNotFoundError("No equity holdings files found for individual users.")
    else:
        excelPath = os.path.join(HOLDINGS_DIR, f"{uname}.xlsx")
        return pd.read_excel(excelPath, 0)


def getUserMutualFundDataFrame(username):
    """
    Fetch mutual fund holdings DataFrame for a specific user,
    or dynamically aggregate all individual user transactions (excluding COMBINED_MF.xlsx).
    """
    uname = str(username or '').strip().upper()
    if uname == 'COMBINED':
        dfs = []
        user_names = getCombinedUsers()
                    
        for u in user_names:
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
            
        raise FileNotFoundError("No MF holdings files found for individual users.")
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