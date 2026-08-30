from datetime import datetime

def convertDatetoSimpleDate(date):
    if date == "INCEPTION":
        return date
    formatted_date = date.strftime("%d-%m-%Y")
    return formatted_date


def differenceBetweenDates(date1, date2):
    return (date2 - date1).days


def get_map_val(mapping, key, default=None):
    if not mapping or not key:
        return default
    k_str = str(key).strip()
    if k_str in mapping:
        return mapping[k_str]
    if k_str.upper() in mapping:
        return mapping[k_str.upper()]
    for m_k, m_v in mapping.items():
        if str(m_k).strip().upper() == k_str.upper():
            return m_v
    return default

def get_trades(summary_map, key):
    if not summary_map or not key:
        return []
    k_str = str(key).strip()
    if k_str in summary_map:
        return summary_map[k_str]
    for m_k, m_v in summary_map.items():
        if str(m_k).strip().upper() == k_str.upper():
            return m_v
    return []

def convertFinalHoldings(finalHoldings, transactionSummary, realtime, equityTypeMap=None, allottedQtyMap=None, allottedCostMap=None):
    if equityTypeMap is None:
        equityTypeMap = {}
    if allottedQtyMap is None:
        allottedQtyMap = {}
    if allottedCostMap is None:
        allottedCostMap = {}
        
    output = []
    if not realtime:    
        for keys, values in finalHoldings.items():
            temp = {}
            temp["stock"] = keys
            temp["price"] = values[0]
            temp["quantity"] = values[1]
            temp["type"] = get_map_val(equityTypeMap, keys, "NORMAL")
            temp["isIPO"] = (str(get_map_val(equityTypeMap, keys, "")).strip().upper() == "IPO")
            temp["transactionSummary"] = get_trades(transactionSummary, keys)
            output.append(temp)
    else:
        for item in finalHoldings:
            if item[0] in ["TOTAL: ", "EQUITY", "TOTAL"]: 
                continue
            stock_name = item[0]
            stock_type = get_map_val(equityTypeMap, stock_name, "NORMAL")
            trades = get_trades(transactionSummary, stock_name)
            
            realised_pnl = sum((t.get('pnl', 0) or 0) for t in trades if t.get('status') == 'Closed' or t.get('sellDate'))
            total_sold = sum((t.get('sellPrice', 0) or 0) * (t.get('quantity', 0) or 0) for t in trades if t.get('status') == 'Closed' or t.get('sellDate'))
            total_allotted_qty = sum((t.get('quantity', 0) or 0) for t in trades if t.get('buyDate'))
            total_invested_all_time = sum((t.get('buyPrice', 0) or 0) * (t.get('quantity', 0) or 0) for t in trades if t.get('buyDate'))
            
            # Use direct source allotment from excel if available
            df_allotted_qty = get_map_val(allottedQtyMap, stock_name)
            if df_allotted_qty is not None and df_allotted_qty > 0:
                total_allotted_qty = df_allotted_qty
                
            df_allotted_cost = get_map_val(allottedCostMap, stock_name)
            if df_allotted_cost is not None and df_allotted_cost > 0:
                total_invested_all_time = df_allotted_cost

            unrealised_pnl = item[6]
            net_pnl = round(realised_pnl + unrealised_pnl, 2)
            
            pnl_basis = total_invested_all_time if total_invested_all_time > 0 else item[3]
            overall_pnl_pct = round((net_pnl / pnl_basis * 100), 2) if pnl_basis > 0 else 0
            
            if item[1] > 0 and (total_allotted_qty > item[1] or total_sold > 0 or realised_pnl != 0):
                pos_status = "Partially Closed"
            elif item[1] > 0:
                pos_status = "Active"
            else:
                pos_status = "Closed"
            
            avg_issue_price = (total_invested_all_time / total_allotted_qty) if (total_allotted_qty and total_invested_all_time) else item[2]
            
            temp = {}
            temp["stock"] = stock_name
            temp["quantity"] = item[1]
            temp["allottedQty"] = total_allotted_qty if total_allotted_qty > 0 else item[1]
            temp["price"] = avg_issue_price
            temp["totalBuy"] = item[3]
            temp["totalInvestedAllTime"] = total_invested_all_time if total_invested_all_time > 0 else item[3]
            temp["totalSold"] = round(total_sold, 2)
            temp["ltp"] = item[4]
            temp["totalValue"] = item[5]
            temp["unrealisedPnL"] = unrealised_pnl
            temp["realisedPnL"] = round(realised_pnl, 2)
            temp["netPnL"] = net_pnl
            temp["pnlPercent"] = overall_pnl_pct
            temp["sector"] = item[8]
            temp["industry"] = item[9]
            temp["peRatio"] = item[10]
            temp["yearLow"] = item[11]
            temp["yearHigh"] = item[12]
            temp["dailyChangePercent"] = item[14]
            temp["dailyChange"] = item[15]
            temp["status"] = pos_status
            temp["type"] = stock_type
            temp["isIPO"] = (str(stock_type).strip().upper() == "IPO")
            temp["transactionSummary"] = trades            
            output.append(temp)
            
        # Also include any closed/realized IPO stocks so they appear in IPO Corner
        existing_stocks = {str(item["stock"]).strip().upper() for item in output}
        for eq, t_type in equityTypeMap.items():
            if str(t_type).strip().upper() == "IPO" and str(eq).strip().upper() not in existing_stocks:
                trades = get_trades(transactionSummary, eq)
                total_buy = sum((t.get('buyPrice', 0) or 0) * (t.get('quantity', 0) or 0) for t in trades)
                total_sold = sum((t.get('sellPrice', 0) or 0) * (t.get('quantity', 0) or 0) for t in trades if t.get('status') == 'Closed' or t.get('sellDate'))
                total_pnl = sum((t.get('pnl', 0) or 0) for t in trades)
                total_qty = sum((t.get('quantity', 0) or 0) for t in trades if t.get('status') == 'Open')
                total_allotted_qty = sum((t.get('quantity', 0) or 0) for t in trades if t.get('buyDate'))
                
                df_allotted_qty = get_map_val(allottedQtyMap, eq)
                if df_allotted_qty is not None and df_allotted_qty > 0:
                    total_allotted_qty = df_allotted_qty
                    
                df_allotted_cost = get_map_val(allottedCostMap, eq)
                if df_allotted_cost is not None and df_allotted_cost > 0:
                    total_buy = df_allotted_cost
                
                avg_price = (total_buy / total_allotted_qty) if total_allotted_qty > 0 else (trades[0].get('buyPrice', 0) if trades else 0)
                last_exit_price = trades[-1].get('sellPrice', 0) if trades else 0
                temp = {
                    "stock": eq,
                    "quantity": total_qty,
                    "allottedQty": total_allotted_qty,
                    "price": avg_price,
                    "totalBuy": total_buy,
                    "totalInvestedAllTime": total_buy,
                    "totalSold": round(total_sold, 2),
                    "ltp": last_exit_price,
                    "totalValue": 0,
                    "unrealisedPnL": 0,
                    "realisedPnL": round(total_pnl, 2),
                    "netPnL": round(total_pnl, 2),
                    "pnlPercent": round((total_pnl / total_buy * 100), 2) if total_buy > 0 else 0,
                    "sector": "IPO",
                    "industry": "IPO",
                    "peRatio": 0,
                    "yearLow": 0,
                    "yearHigh": 0,
                    "dailyChangePercent": 0,
                    "dailyChange": 0,
                    "status": "Closed",
                    "type": "IPO",
                    "isIPO": True,
                    "transactionSummary": trades
                }
                output.append(temp)
    return output