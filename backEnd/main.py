import sys
import os
import socket
import datetime
from typing import Optional, cast
from sqlalchemy import text, inspect, func

appserver_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(appserver_path, "API"))
from analyseStock import AnalyseStock
from strategies import StrategyRegistry
import fetchEquityDayWisePnlPosition
import initialiseApplication
import commonUtils
import time
from nseScrap import *
import fetchHeatmapDataService
import fetchMutualFundDataService
from datetime import date
import state
import addFinalHoldings

from flask import request, jsonify
from config import app, db
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
from dataQuery.userQuery import User
from dataQuery.dividendsQuery import Dividends
from dataQuery.equityMasterQuery import EquityMaster
from dataQuery.equityMarketDataQuery import EquityMarketData
from dataQuery.mutualFundMasterQuery import MutualFundMaster
from dataQuery.mutualFundMarketDataQuery import MutualFundMarketData
from dataQuery.mutualFundDayWisePositionQuery import MutualFundDayWisePosition
from dataQuery.mutualFundInvestmentsTransactionsQuery import MutualFundInvestmentsTransactions
from dataQuery.equityDayWisePositionQuery import EquityDayWisePosition
import helperFunctions
import uuid
import pandas as pd
import mailDispatcher


server_restart_id = str(uuid.uuid4())  # Unique ID for each restart
jwt = JWTManager(app)

@app.route("/server_status", methods=["GET"])
def server_status():
   return jsonify({"server_restart_id": server_restart_id})

@app.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "").strip()
    if not username:
        return jsonify({"message": "Username is required"}), 400

    userId = helperFunctions.getUserId(username.lower())
    userObject = cast(Optional[User], User.query.filter_by(id=userId).first())
    if not userObject:
        return jsonify({"message": "Invalid username"}), 401
        
    fetchMutualFundDataService.updateMutualFundData(withTimeContrainst=True)
    fetchEquityDayWisePnlPosition.updateEquityDataBulk()
    fetchEquityDayWisePnlPosition.updateDividendsForHoldings()
    initialiseApplication.initialise()
    
    if username.upper() == "COMBINED":
        all_users = User.query.filter(func.lower(User.username) != 'combined').all()
        for u in all_users:
            try:
                fetchEquityDayWisePnlPosition.syncUserDividends(u.getId())
            except Exception as e:
                pass
    else:
        fetchEquityDayWisePnlPosition.syncUserDividends(userId)
        
    user_name = userObject.getUserName()
    access_token = create_access_token(identity=user_name)
    return jsonify({"token": access_token, "username": user_name}), 200

# Protected route example (requires authentication)
@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    return jsonify({"message": "You are authenticated"}), 200

@app.route("/fetchPortfolio", methods=["GET"])
def fetchPortfolio():
    userId = request.args.get("userId", "COMBINED").upper()
    portfolioAsOnDate = request.args.get("selectedDate")
    force_refresh = request.args.get("refresh", "false").lower() == "true"
    print(f"User Id is : {userId}")
    print(f"Portfolio date is : {portfolioAsOnDate}")
    if not portfolioAsOnDate:
        portfolioAsOnDate = date.today().strftime("%Y-%m-%d") 
        
    cache_key = (userId, portfolioAsOnDate)
    if not force_refresh and cache_key in state.portfolioResponseCache:
        cached_time, cached_data = state.portfolioResponseCache[cache_key]
        if time.time() - cached_time < 300:  # 5 minutes TTL
            return jsonify(cached_data) 
        
    try:
        dataframe = helperFunctions.getUserEquityDataFrame(userId)
    except FileNotFoundError:
        return jsonify({"error": "User portfolio not found"}), 404
        
    # Auto-discover and backfill 5-year history for any new equity in user dataframe
    try:
        from autoDiscoveryService import auto_discover_equity
        equity_col = next((c for c in dataframe.columns if str(c).strip().lower() == 'equity'), 'EQUITY')
        if equity_col in dataframe.columns:
            for eq_sym in dataframe[equity_col].dropna().unique():
                eq_clean = str(eq_sym).strip().upper()
                if eq_clean and eq_clean not in ['TOTAL', 'EQUITY', 'SUM']:
                    if not EquityMaster.query.filter_by(equityShortName=eq_clean).first():
                        auto_discover_equity(eq_clean)
    except Exception as e:
        print(f"[AutoDiscovery] Error in portfolio auto-discovery: {e}")

    t1 = time.time()
    if str(userId).upper() != "COMBINED":
        fetchEquityDayWisePnlPosition.persistEquityDayWisePnlPosition(userId, dataframe)
    resolved_uid = helperFunctions.getUserId(userId.lower())
    if resolved_uid:
        try:
            if userId.upper() == "COMBINED":
                all_users = User.query.filter(func.lower(User.username) != 'combined').all()
                for u in all_users:
                    fetchEquityDayWisePnlPosition.syncUserDividends(u.getId())
            else:
                fetchEquityDayWisePnlPosition.syncUserDividends(resolved_uid)
        except Exception as e:
            print(f"Error syncing user dividends in fetchPortfolio: {e}")
            
    realisedPnL, finalHoldings, transactionSummary = fetchEquityDayWisePnlPosition.createPositionsForSingleDay(dataframe, portfolioAsOnDate)
    portfolioDateObj = datetime.datetime.strptime(str(portfolioAsOnDate), "%Y-%m-%d").date()
    if not state.marketDataCache or portfolioDateObj not in state.marketDataCache:
        initialiseApplication.initiateCacheEquity(portfolioAsOnDate)
    while portfolioDateObj not in state.marketDataCache.keys():
        portfolioDateObj -= datetime.timedelta(1)
        if (date.today() - portfolioDateObj).days > 30: 
            break
    liveQuotesMapScrapping = state.marketDataCache.get(portfolioDateObj, {})
    # Build mapping for trade types (e.g. IPO) and allotment totals
    type_col = next((c for c in dataframe.columns if str(c).strip().lower() == 'type'), None)
    equity_col = next((c for c in dataframe.columns if str(c).strip().lower() == 'equity'), 'EQUITY')
    qty_col = next((c for c in dataframe.columns if str(c).strip().lower() == 'qty'), 'QTY')
    price_col = next((c for c in dataframe.columns if str(c).strip().lower() in ['traded_at', 'price', 'rate']), 'TRADED_AT')
    
    equityTypeMap = {}
    allottedQtyMap = {}
    allottedCostMap = {}
    
    for _, row in dataframe.iterrows():
        eq = str(row[equity_col]).strip()
        val = str(row[type_col]).strip().upper() if type_col is not None and pd.notna(row[type_col]) else ""
        if val == 'IPO' or 'IPO' in val:
            equityTypeMap[eq] = 'IPO'
            
        raw_qty = row[qty_col] if qty_col in row and pd.notna(row[qty_col]) else 0
        raw_price = row[price_col] if price_col in row and pd.notna(row[price_col]) else 0
        if raw_qty > 0:
            allottedQtyMap[eq] = allottedQtyMap.get(eq, 0) + raw_qty
            allottedCostMap[eq] = allottedCostMap.get(eq, 0) + (raw_qty * raw_price)

    rawHoldingData = addFinalHoldings.addFinalHoldingData(
        finalHoldings, 
        liveQuotesMapScrapping, 
        state.equityMasterCache,
        transactionSummary,
        portfolioAsOnDate
    )
    finalHoldingsData = commonUtils.convertFinalHoldings(
        rawHoldingData, 
        transactionSummary, 
        True, 
        equityTypeMap, 
        allottedQtyMap, 
        allottedCostMap
    )
    rawRealisedData = {}
    for equity, trades in realisedPnL.items():
        rawRealisedData[equity] = [
            {
                "buyDate": t[0].strftime("%Y-%m-%d") if hasattr(t[0], 'strftime') else str(t[0]),
                "sellDate": t[1].strftime("%Y-%m-%d") if hasattr(t[1], 'strftime') else str(t[1]),
                "qty": t[2],
                "buyPrice": t[3],
                "sellPrice": t[4],
                "pnl": round((t[4] - t[3]) * t[2], 2)
            }
            for t in trades
        ]
    print(f"Time taken to calculate Holdings: {time.time() - t1}s")
    res_payload = {
        "holdings": finalHoldingsData, 
        "realisedSummary": rawRealisedData  # Now contains lists of raw trade objects
    }
    state.portfolioResponseCache[cache_key] = (time.time(), res_payload)
    return jsonify(res_payload)

@app.route("/fetchChartData", methods=["GET"])
def fetchChartData():
    username = request.args.get("userId", "COMBINED").upper()
    portfolioAsOnDate = request.args.get("selectedDate")
    if portfolioAsOnDate == '' or portfolioAsOnDate is None:
        portfolioAsOnDate = date.today()
    try:
        dataframe = helperFunctions.getUserEquityDataFrame(username)
    except FileNotFoundError:
        return jsonify([[], [], []])
        
    xLabel, yLabel1, yLabel2 = fetchEquityDayWisePnlPosition.getPositions(dataframe, username, portfolioAsOnDate)
    return jsonify([xLabel, yLabel1, yLabel2])

@app.route("/fetchDividends", methods=['GET'])
def fetchDividends():
    username = request.args.get("userId", "").upper()
    raw_tickers = request.args.get("tickers", "")
    tickers = [ticker.strip().upper() for ticker in raw_tickers.split(",") if ticker.strip()]

    if username == "COMBINED":
        all_users = User.query.filter(func.lower(User.username) != 'combined').all()
        for u in all_users:
            fetchEquityDayWisePnlPosition.syncUserDividends(u.getId())
    else:
        fetchEquityDayWisePnlPosition.syncUserDividends(username)
        
    return jsonify(fetchEquityDayWisePnlPosition.fetchDividendsForHoldings(tickers))
    

@app.route("/fetchScripHistory", methods=['GET'])
def fetch_scrip_history():
    userName = request.args.get('userId')
    symbol = request.args.get('symbol')
    equityNameIdMap = {e.getEquityShortName(): eid for eid, e in state.equityMasterCache.items()}
    equityId = equityNameIdMap.get(symbol)
    
    if not equityId:
        return jsonify([])
    historyRecords = EquityMarketData.query.filter_by(equityId=equityId).order_by(EquityMarketData.marketDate.asc()).all()
    if not historyRecords:
        return jsonify([])
    df = pd.DataFrame([{
        "date": r.marketDate, 
        "price": r.close
    } for r in historyRecords])

    # 4. Calculate EMAs (Exponential Moving Averages)
    # span defines the N-day period; adjust_false uses the standard recursive formula
    df['ema20'] = df['price'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['price'].ewm(span=50, adjust=False).mean()
    df['ema100'] = df['price'].ewm(span=100, adjust=False).mean()
    df['ema200'] = df['price'].ewm(span=200, adjust=False).mean()
    df = df.fillna(0)
    history = []
    for _, row in df.iterrows():
        history.append({
            "date": row['date'].strftime('%Y-%m-%d'),
            "price": round(float(row['price']), 2),
            "ema20": round(float(row['ema20']), 2),
            "ema50": round(float(row['ema50']), 2),
            "ema100": round(float(row['ema100']), 2),
            "ema200": round(float(row['ema200']), 2)
        })

    return jsonify(history)

@app.route("/fetchScripDividends", methods=['GET'])
def fetch_scrip_dividends():
    username = request.args.get('userId', 'COMBINED').upper()
    symbol = request.args.get('symbol')
    
    if not symbol:
        return jsonify([])
    
    equityNameIdMap = {e.getEquityShortName(): eid for eid, e in state.equityMasterCache.items()}
    equityId = equityNameIdMap.get(symbol)
    
    if not equityId:
        return jsonify([])
    
    # Fetch dividend records for this user and stock
    from dataQuery.dividendsHistoricalQuery import DividendsHistorical
    if username == "COMBINED":
        dividendRecords = DividendsHistorical.query.filter_by(
            equityId=equityId
        ).order_by(DividendsHistorical.payoutDate.desc()).all()
    else:
        userId = helperFunctions.getUserId(username.lower())
        if not userId:
            return jsonify([])
        dividendRecords = DividendsHistorical.query.filter_by(
            userId=userId, 
            equityId=equityId
        ).order_by(DividendsHistorical.payoutDate.desc()).all()
    
    dividends = []
    for record in dividendRecords:
        dividends.append({
            'payoutDate': record.payoutDate.strftime('%Y-%m-%d') if record.payoutDate else '',
            'dividendAmount': float(record.dividendPerShare) if record.dividendPerShare else 0,
            'quantity': int(record.quantityHeld) if record.quantityHeld else 0,
            'totalDividend': float(record.totalDividendAmount) if record.totalDividendAmount else 0
        })
    
    return jsonify(dividends)

@app.route("/fetchTotalDividends", methods=['GET'])
def fetch_total_dividends():
    user_param = request.args.get('userId', '')
    if not user_param or str(user_param).lower() in ['null', 'undefined', '']:
        user_param = 'COMBINED'
        
    uname_upper = str(user_param).upper()
    from dataQuery.dividendsHistoricalQuery import DividendsHistorical
    from dataQuery.equityMasterQuery import EquityMaster

    if uname_upper == "COMBINED":
        all_users = User.query.filter(func.lower(User.username) != 'combined').all()
        for u in all_users:
            try:
                fetchEquityDayWisePnlPosition.syncUserDividends(u.getId())
            except Exception as e:
                pass
        totalDividendRecords = DividendsHistorical.query.all()
    else:
        resolved_id = helperFunctions.getUserId(str(user_param).lower())
        if not resolved_id and str(user_param).isdigit():
            resolved_id = int(user_param)
            
        if not resolved_id:
            first_u = User.query.first()
            resolved_id = first_u.getId() if first_u else None
            
        if not resolved_id:
            return jsonify({"totalDividends": 0, "dividendsList": []})
        
        # Fast check: only sync if not already recorded
        has_records = DividendsHistorical.query.filter_by(userId=resolved_id).first() is not None
        if not has_records:
            try:
                fetchEquityDayWisePnlPosition.syncUserDividends(resolved_id)
            except Exception as e:
                print(f"Error syncing user dividends: {e}")
        
        # Query all dividends for this user across all stocks
        totalDividendRecords = DividendsHistorical.query.filter_by(userId=resolved_id).all()
    
    totalDividends = sum(float(record.totalDividendAmount) if record.totalDividendAmount else 0 
                        for record in totalDividendRecords)
    
    dividendsList = []
    for record in totalDividendRecords:
        equity_obj = state.equityMasterCache.get(record.equityId) if state.equityMasterCache else None
        if not equity_obj:
            equity_obj = EquityMaster.query.filter_by(id=record.equityId).first()
        stock_name = equity_obj.getEquityShortName() if equity_obj else f"Equity #{record.equityId}"
        long_name = equity_obj.getEquityLongName() if equity_obj else stock_name
        
        p_date = record.payoutDate.strftime("%Y-%m-%d") if hasattr(record.payoutDate, 'strftime') else str(record.payoutDate)
        
        dividendsList.append({
            "id": record.id,
            "stock": stock_name,
            "companyName": long_name,
            "payoutDate": p_date,
            "dividendPerShare": float(record.dividendPerShare) if record.dividendPerShare else 0.0,
            "quantity": float(record.quantityHeld) if record.quantityHeld else 0.0,
            "amount": float(record.totalDividendAmount) if record.totalDividendAmount else 0.0,
            "totalDividend": float(record.totalDividendAmount) if record.totalDividendAmount else 0.0
        })
        
    dividendsList.sort(key=lambda x: x['payoutDate'] or '', reverse=True)
    
    return jsonify({
        "totalDividends": round(totalDividends, 2),
        "dividendsList": dividendsList
    })

@app.route("/fetchStockAnalysis", methods=["GET"])
def fetchStockAnalysis():
    raw_stock = request.args.get("stock", "").upper()
    tickers = [s.strip() for s in raw_stock.split(",") if s.strip()]
    if not tickers:
        return jsonify({})
    
    if len(tickers) == 1:
        stock = tickers[0]
        analyseStock = AnalyseStock(stock)
        holdings = analyseStock.fetchStockAnalysisData(stock)
        return jsonify(AnalyseStock._sanitize_for_json(holdings))
    else:
        import time
        from concurrent.futures import ThreadPoolExecutor

        def analyze_one(s):
            try:
                # Small polite delay between requests to avoid Cloudflare rate-limiting
                time.sleep(0.15)
                engine = AnalyseStock(s)
                return engine.fetchStockAnalysisData(s)
            except Exception as e:
                print(f"Error analyzing {s}: {e}")
                return None
                
        # Limit concurrency to 2-3 workers so Screener does not throttle the IP
        workers = min(len(tickers), 3)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(analyze_one, tickers))
            
        valid_results = [r for r in results if r is not None]
        return jsonify(AnalyseStock._sanitize_for_json(valid_results))

@app.route("/clearStockAnalysisCache", methods=["POST", "GET"])
def clearStockAnalysisCache():
    try:
        AnalyseStock._cache.clear()
        return jsonify({"status": "success", "message": "Stock analysis cache cleared successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/fetchAvailableStrategies", methods=["GET"])
def fetchAvailableStrategies():
    strategies = StrategyRegistry.get_all_strategy_infos()
    return jsonify(strategies)

@app.route("/backtestStockStrategy", methods=["GET"])
def backtestStockStrategy():
    stock = request.args.get("stock", "").strip().upper()
    if not stock:
        return jsonify({"status": "error", "message": "Stock parameter is required"}), 400
    strategy_id = request.args.get("strategy", "sr_poc").strip().lower()
    try:
        years = int(request.args.get("years", 2))
    except (ValueError, TypeError):
        years = 2
        
    result = StrategyRegistry.run_backtest(
        strategy_id=strategy_id,
        stock=stock,
        lookback_years=years
    )
    return jsonify(AnalyseStock._sanitize_for_json(result))

@app.route("/fetchHeatmapData", methods=["GET"])
def fetchHeatmapData():
    heatmap = request.args.get("heatmap").upper()
    return jsonify(fetchHeatmapDataService.fetchHeatmap(heatmap))


@app.route("/fetchMutualFundData", methods=["GET"])
def fetchMutualFundData():
    userId = request.args.get("userId", "COMBINED").upper()
    force_refresh = request.args.get("refresh", "false").lower() == "true"
    
    if not force_refresh and userId in state.mfResponseCache:
        cached_time, cached_data = state.mfResponseCache[userId]
        if time.time() - cached_time < 300:  # 5 minutes TTL
            return jsonify(cached_data)
            
    try:
        dataframe = helperFunctions.getUserMutualFundDataFrame(userId)
    except FileNotFoundError:
        return jsonify({})
    res_data = fetchMutualFundDataService.fetchMutualFund(dataframe, userId, True)
    state.mfResponseCache[userId] = (time.time(), res_data)
    return jsonify(res_data)

@app.route("/fetchDashboardOverview", methods=["GET"])
def fetchDashboardOverview():
    user_param = request.args.get('userId', 'COMBINED').strip().upper()
    force_refresh = request.args.get("refresh", "false").lower() == "true"
    resolved_id = helperFunctions.getUserId(user_param.lower())
    if not resolved_id:
        resolved_id = 1
        
    cache_key = f"dashboard_{resolved_id}"
    now = time.time()
    if not force_refresh and cache_key in state.dashboardOverviewCache:
        cached_time, cached_data = state.dashboardOverviewCache[cache_key]
        if now - cached_time < 300:  # 5 minutes TTL
            return jsonify(cached_data)

    if resolved_id == 1 and (force_refresh or state.dashboardOverviewCache.get(cache_key) is None):
        latest_market_date = helperFunctions.getLatestExistingEquityMarketData()
        max_eq_date = db.session.query(func.max(EquityDayWisePosition.asOfDate)).filter_by(userId=1).scalar()
        if max_eq_date is None or (latest_market_date and max_eq_date < latest_market_date):
            from autoDiscoveryService import backfill_combined_positions
            backfill_combined_positions()

    # 1. Equity Summary from Equity_DayWisePosition
    max_eq_date = db.session.query(func.max(EquityDayWisePosition.asOfDate)).filter_by(userId=resolved_id).scalar()
    eq_invested, eq_current = 0.0, 0.0
    if max_eq_date:
        eq_res = db.session.query(
            func.sum(EquityDayWisePosition.totalInvestment),
            func.sum(EquityDayWisePosition.currentInvestment)
        ).filter_by(userId=resolved_id, asOfDate=max_eq_date).first()
        if eq_res:
            eq_invested = float(eq_res[0] or 0.0)
            eq_current = float(eq_res[1] or 0.0)
            
    eq_profit = eq_current - eq_invested
    eq_profit_pct = (eq_profit / eq_invested * 100) if eq_invested > 0 else 0.0
    
    # 2. Mutual Fund Summary from MF_DayWisePosition
    max_mf_date = db.session.query(func.max(MutualFundDayWisePosition.asOfDate)).filter_by(userId=resolved_id).scalar()
    mf_invested, mf_current = 0.0, 0.0
    if max_mf_date:
        mf_res = db.session.query(
            func.sum(MutualFundDayWisePosition.totalInvestment),
            func.sum(MutualFundDayWisePosition.currentInvestment)
        ).filter_by(userId=resolved_id, asOfDate=max_mf_date).first()
        if mf_res:
            mf_invested = float(mf_res[0] or 0.0)
            mf_current = float(mf_res[1] or 0.0)
            
    mf_profit = mf_current - mf_invested
    mf_profit_pct = (mf_profit / mf_invested * 100) if mf_invested > 0 else 0.0
    
    # 3. Dividends from DividendsHistorical
    from dataQuery.dividendsHistoricalQuery import DividendsHistorical
    div_query = db.session.query(func.sum(DividendsHistorical.totalDividendAmount))
    if user_param != "COMBINED":
        div_query = div_query.filter_by(userId=resolved_id)
    total_div = float(div_query.scalar() or 0.0)
    
    data = {
        "equity": {
            "invested": eq_invested,
            "current": eq_current,
            "profit": eq_profit,
            "profitPct": eq_profit_pct
        },
        "mutualFunds": {
            "invested": mf_invested,
            "current": mf_current,
            "profit": mf_profit,
            "profitPct": mf_profit_pct
        },
        "totalDividends": total_div
    }
    
    state.dashboardOverviewCache[cache_key] = (now, data)
    return jsonify(data)

# @app.route("/marketStatus", methods=["GET"])
# def marketStatus():
#     return jsonify({"is_open": is_market_open() and running_status()})

@app.route("/fetchReports", methods=["GET"])
def generate_report_route():
    userId = request.args.get("userId").lower()
    reportId = request.args.get("reportId")
    recipientsRaw = request.args.get('sendTo')
    recipientsListRaw = [r.strip() for r in recipientsRaw.split(',') if r.strip()]
    allUsersQueried = User.query.all()
    recipients = []
    for user in allUsersQueried:
        if user.getUserName().lower() in recipientsListRaw:
            recipients.append(user.getEmailAddress().lower())
    try:
        mailDispatcher.generateAndSendReport(reportId, recipients)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

def get_available_port(preferred_port: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", preferred_port))
            return preferred_port
        except OSError:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]


if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            inspector = inspect(db.engine)
            print("Tables in the database:", inspector.get_table_names())
            initialiseApplication.initialise()
        except Exception as e:
            print(f"Startup initialization error: {e}")

    # if not os.environ.get("WERKZEUG_RUN_MAIN"):
    # marketDataThread = threading.Thread(target=executeMarketDataService, daemon=True)
    # marketDataThread.start()
    preferred_port = int(os.getenv("PORT", "5001"))
    port = get_available_port(preferred_port)
    print(f"Starting Flask server on port {port}")
    app.run(debug=False, use_reloader=False, port=port)