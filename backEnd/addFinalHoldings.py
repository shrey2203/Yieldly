import state
from datetime import datetime, date
from dataQuery.equityMarketDataQuery import EquityMarketData

def addFinalHoldingData(finalHoldingsData, liveQuotesMap, equityMasterCache, transactionSummary=None, portfolioAsOnDate=None):
    headers = [
        'EQUITY', 'QTY', 'AVERAGE BUY', 'TOTAL BUY', "LTP", "TOTAL VALUE", 
        "UNREALISED P/L", "P/L %", "SECTOR", "INDUSTRY", "P/E Ratio", 
        "52W High", "52W Low", "CHIP", "DAILY CHANGE PERCENT", "DAILY CHANGE"
    ]
    finalHoldingData = [headers]
    grandTotalBuy, grandTotalValue = 0, 0
    def get_sector_from_cache(stock_name):
        for equity_obj in equityMasterCache.values():
            if equity_obj.equityShortName == stock_name:
                return getattr(equity_obj, 'sector', 'Other') 
        return "Other"

    # Determine target portfolio date
    target_date = None
    if portfolioAsOnDate:
        if isinstance(portfolioAsOnDate, str):
            try:
                target_date = datetime.strptime(str(portfolioAsOnDate), "%Y-%m-%d").date()
            except Exception:
                pass
        elif hasattr(portfolioAsOnDate, 'date'):
            target_date = portfolioAsOnDate.date()
        else:
            target_date = portfolioAsOnDate
    if not target_date:
        target_date = date.today()

    for equity, parameters in finalHoldingsData.items():
        qty = parameters[1]
        averageBuy = parameters[0]
        
        # Initialize defaults
        ltp = 0
        unrealisedPnl = 0
        totalValue = 0
        pnlPercentage = 0
        
        # Fetch Sector from DB Cache first (More reliable than scraper)
        sector = get_sector_from_cache(equity)
        industry = "Other"
        
        peRatio = 0
        yearLow = 0
        yearHigh = 0
        category = ""
        dailyChangePercent = 0
        dailyChange = 0
        last_close = 0

        if equity in liveQuotesMap:
            stock_data = liveQuotesMap[equity]
            ltp = stock_data.get("lastPrice", 0)
            last_close = stock_data.get("lastClose")
            if not last_close or last_close == 0:
                for _, prev_map in state.prevDayCloseCache.items():
                    if equity in prev_map and prev_map[equity] > 0:
                        last_close = prev_map[equity]
                        break
            if not last_close or last_close == 0:
                last_close = ltp

            unrealisedPnl = (ltp - averageBuy) * qty
            totalValue = ltp * qty            
            if averageBuy != 0:
                pnlPercentage = (unrealisedPnl / (qty * averageBuy)) * 100
            if sector == "Other":
                sector = stock_data.get('Sector', stock_data.get('Industry', 'Other'))
            
            industry = stock_data.get('Industry', 'Other')
            yearLow = stock_data.get("52w Low", 0)
            yearHigh = stock_data.get("52w High", 0)
        else:
            eq_obj = None
            for m in equityMasterCache.values():
                if m.getEquityShortName() == equity:
                    eq_obj = m
                    break
            latest_rec = None
            if eq_obj:
                try:
                    latest_rec = EquityMarketData.query.filter_by(equityId=eq_obj.getId()).order_by(EquityMarketData.marketDate.desc()).first()
                except Exception:
                    latest_rec = None
            if latest_rec:
                ltp = float(latest_rec.getClose())
                totalValue = qty * ltp
                unrealisedPnl = (ltp - averageBuy) * qty
                if averageBuy != 0:
                    pnlPercentage = (unrealisedPnl / (qty * averageBuy)) * 100
                try:
                    prev_rec = EquityMarketData.query.filter(
                        EquityMarketData.equityId == eq_obj.getId(),
                        EquityMarketData.marketDate < latest_rec.getMarketDate()
                    ).order_by(EquityMarketData.marketDate.desc()).first()
                    last_close = float(prev_rec.getClose()) if prev_rec else ltp
                except Exception:
                    last_close = ltp
            else:
                ltp = averageBuy
                totalValue = qty * averageBuy
                unrealisedPnl = 0
                pnlPercentage = 0

        # Check open lots for this equity to determine what was bought today vs held overnight
        open_lots = []
        if transactionSummary and equity in transactionSummary:
            trades = transactionSummary[equity]
            for t in trades:
                if t.get('status') == 'Open' or not t.get('sellDate'):
                    b_date = t.get('buyDate')
                    if isinstance(b_date, str):
                        try:
                            b_date = datetime.strptime(b_date, "%Y-%m-%d").date()
                        except Exception:
                            pass
                    open_lots.append({
                        'buyDate': b_date,
                        'qty': t.get('quantity', 0),
                        'buyPrice': t.get('buyPrice', 0)
                    })

        if open_lots and ltp > 0:
            day_pnl = 0.0
            day_base_cost = 0.0
            for lot in open_lots:
                l_qty = lot['qty']
                l_buy_price = lot['buyPrice']
                l_date = lot['buyDate']
                # If bought on target_date (today), the baseline is the purchase price
                if l_date == target_date:
                    lot_base = l_buy_price
                else:
                    # Carried forward from yesterday, baseline is yesterday's close
                    lot_base = last_close if (last_close and last_close > 0) else l_buy_price
                day_pnl += (ltp - lot_base) * l_qty
                day_base_cost += lot_base * l_qty

            dailyChange = round(day_pnl, 2)
            dailyChangePercent = round((day_pnl / day_base_cost) * 100, 2) if day_base_cost > 0 else 0.0
        elif last_close != 0:
            dailyChangePercent = ((ltp - last_close) / last_close) * 100
            dailyChange = (ltp - last_close) * qty

        grandTotalBuy += (averageBuy * qty)
        grandTotalValue += totalValue

        finalHoldingData.append([
            equity, qty, averageBuy, qty * averageBuy, ltp, totalValue, 
            unrealisedPnl, round(pnlPercentage, 2), sector, industry, 
            peRatio, yearHigh, yearLow, category, dailyChangePercent, dailyChange
        ])
    totalPnl = grandTotalValue - grandTotalBuy
    totalPnlPercentage = (totalPnl * 100) / grandTotalBuy if grandTotalBuy != 0 else 0
    finalHoldingData.append([
        "TOTAL", "", "", grandTotalBuy, "", grandTotalValue, 
        totalPnl, totalPnlPercentage, "", "", "", "", "", "", "", ""
    ]) 
    return finalHoldingData

def getCategory(data):
    if "NIFTY 50" in data or "NIFTY 100" in data:
        return "LargeCap"
    else:
        return "yet to implement"