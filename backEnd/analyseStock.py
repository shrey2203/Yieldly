"""
Stock Analysis Engine for Fundamental & Technical Metrics.
Fetches and calculates:
- Stock P/E Ratio
- Quarterly EPS for the last 4 quarters
- Promoter, FII, and DII Holdings and QoQ Changes
- 14-period Relative Strength Index (RSI)
- Debt to Equity (D/E) Ratio
- Market Cap, Current Price, ROCE, and ROE
"""

import re
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, date
from bs4 import BeautifulSoup
import financialMath


class AnalyseStock:
    def __init__(self, stock: str):
        self.stock = stock.strip().upper()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    def fetchStockAnalysisData(self, stock: str = None) -> dict:
        """
        Main entrypoint to fetch comprehensive fundamental and technical metrics for a stock.
        """
        target_stock = (stock or self.stock).strip().upper()
        
        result = {
            "stock": target_stock,
            "companyName": target_stock,
            "currentPrice": None,
            "marketCap": None,
            "peRatio": None,
            "debtToEquity": None,
            "roce": None,
            "roe": None,
            "rsi": None,
            "promoterHolding": None,
            "promoterChange": None,
            "fiiHolding": None,
            "fiiChange": None,
            "diiHolding": None,
            "diiChange": None,
            "publicHolding": None,
            "quarterlyEps": [],
            "epsLast4Qtrs": [],
            "source": "Screener",
            # Historical PE median comparison
            "peMedian1Y": None,
            "peMedian3Y": None,
            "peMedian5Y": None,
            "belowMedian1Y": None,
            "belowMedian3Y": None,
            "belowMedian5Y": None,
        }

        # 1. Fetch Fundamentals from Screener
        screener_data = self._fetch_from_screener(target_stock)
        if screener_data:
            result.update(screener_data)

        # 2. Fetch / Fallback & Technicals (RSI, PE, D/E) via yfinance / Database
        yf_data = self._fetch_from_yfinance(target_stock)
        if yf_data:
            for k, v in yf_data.items():
                if result.get(k) is None or result.get(k) == 0:
                    result[k] = v

        # 3. Compute historical median PE (1yr, 3yr, 5yr) for valuation signal
        pe_medians = self._fetch_historical_pe_medians(target_stock)
        result.update(pe_medians)

        # Format EPS for convenient frontend consumption
        if result.get("quarterlyEps") and not result.get("epsLast4Qtrs"):
            result["epsLast4Qtrs"] = [item["eps"] for item in result["quarterlyEps"]]

        return result

    def _fetch_from_screener(self, stock: str) -> dict:
        """
        Scrapes key ratios, quarterly results, and shareholding pattern from Screener.in.
        """
        urls = [
            f"https://www.screener.in/company/{stock}/consolidated/",
            f"https://www.screener.in/company/{stock}/"
        ]
        
        soup = None
        for url in urls:
            try:
                resp = requests.get(url, headers=self.headers, timeout=6)
                if resp.status_code == 200 and "Company not found" not in resp.text:
                    soup = BeautifulSoup(resp.content, "html.parser")
                    break
            except Exception as e:
                continue

        if not soup:
            return {}

        data = {}

        try:
            # 1. Company Name
            h1 = soup.find("h1", class_="h2") or soup.find("h1")
            if h1:
                data["companyName"] = h1.get_text(strip=True)

            # 2. Top Ratios (P/E, Market Cap, Debt to Equity, ROCE, ROE)
            top_ratios = soup.find("ul", id="top-ratios")
            if top_ratios:
                for item in top_ratios.find_all("li"):
                    name_span = item.find("span", class_="name")
                    val_span = item.find("span", class_="value") or item.find("span", class_="nowrap")
                    if name_span and val_span:
                        name = name_span.get_text(strip=True).lower()
                        val_txt = val_span.get_text(strip=True).replace(",", "")
                        
                        # Extract numerical value
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

            # 3. Quarterly EPS (Quarterly Results Table)
            quarterly_sec = soup.find("section", id="quarters")
            if quarterly_sec:
                table = quarterly_sec.find("table", class_="data-table")
                if table:
                    headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]
                    quarter_names = headers[1:] if len(headers) > 1 else []
                    
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
                        
                        # Keep last 4 quarters
                        last_4 = quarterly_eps[-4:] if len(quarterly_eps) >= 4 else quarterly_eps
                        data["quarterlyEps"] = last_4
                        data["epsLast4Qtrs"] = [item["eps"] for item in last_4]

            # 4. Shareholding Pattern (Promoter, FII, DII QoQ Changes)
            shareholding_sec = soup.find("section", id="shareholding")
            if shareholding_sec:
                table = shareholding_sec.find("table", class_="data-table")
                if table:
                    for tr in table.find("tbody").find_all("tr"):
                        tds = tr.find_all("td")
                        if len(tds) >= 3:
                            holder_name = tds[0].get_text(strip=True)
                            
                            def parse_pct(txt):
                                clean = txt.replace("%", "").replace(",", "").strip()
                                try:
                                    return float(clean)
                                except ValueError:
                                    return 0.0

                            latest_val = parse_pct(tds[-1].get_text(strip=True))
                            prev_val = parse_pct(tds[-2].get_text(strip=True))
                            diff = round(latest_val - prev_val, 2)
                            
                            if "promoter" in holder_name.lower():
                                data["promoterHolding"] = latest_val
                                data["promoterChange"] = diff
                            elif "fii" in holder_name.lower():
                                data["fiiHolding"] = latest_val
                                data["fiiChange"] = diff
                            elif "dii" in holder_name.lower():
                                data["diiHolding"] = latest_val
                                data["diiChange"] = diff
                            elif "public" in holder_name.lower():
                                data["publicHolding"] = latest_val

        except Exception as e:
            print(f"Error parsing screener data for {stock}: {e}")

        return data

    def _fetch_from_yfinance(self, stock: str) -> dict:
        """
        Fetches PE, D/E, market prices, and calculates 14-period RSI using yfinance.
        """
        data = {}
        for suffix in [".NS", ".BO"]:
            ticker_symbol = f"{stock}{suffix}"
            try:
                ticker = yf.Ticker(ticker_symbol)
                
                # Fetch info
                info = ticker.info
                if info and isinstance(info, dict):
                    if not data.get("peRatio"):
                        data["peRatio"] = info.get("trailingPE") or info.get("forwardPE")
                        if data["peRatio"]:
                            data["peRatio"] = round(float(data["peRatio"]), 2)
                            
                    if not data.get("debtToEquity"):
                        de = info.get("debtToEquity")
                        if de is not None:
                            # yfinance returns debtToEquity as % (e.g. 45.2 -> 0.45 or 45.2)
                            data["debtToEquity"] = round(float(de) / 100.0, 2) if float(de) > 5.0 else round(float(de), 2)
                            
                    if not data.get("currentPrice"):
                        data["currentPrice"] = info.get("currentPrice") or info.get("regularMarketPrice")
                    if not data.get("marketCap"):
                        data["marketCap"] = info.get("marketCap")
                        
                # Calculate RSI using recent price history
                hist = ticker.history(period="3mo")
                if hist is not None and not hist.empty and len(hist) >= 15:
                    closes = hist["Close"].tolist()
                    rsi_val = financialMath.calculate_rsi(closes, period=14)
                    if rsi_val is not None:
                        data["rsi"] = rsi_val

                if data.get("peRatio") or data.get("rsi"):
                    break
            except Exception as e:
                continue

        return data

    def _fetch_historical_pe_medians(self, stock: str) -> dict:
        """
        Fetches 1Y, 3Y, and 5Y Median PE values directly from Screener's chart API
        (same values shown below the PE chart on screener.in).
        Also extracts current PE from the weekly PE time-series.
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
            import urllib.parse

            # Step 1: Resolve company ID from Screener search API
            search_url = f"https://www.screener.in/api/company/search/?q={urllib.parse.quote(stock)}"
            search_resp = requests.get(search_url, headers=self.headers, timeout=6)
            if search_resp.status_code != 200:
                return result

            search_data = search_resp.json()
            if not search_data:
                return result

            company_id = search_data[0].get("id")
            if not company_id:
                return result

            # Step 2: Determine if consolidated or standalone
            company_url = search_data[0].get("url", "")
            is_consolidated = "consolidated" in company_url

            # Step 3: Fetch median PE for each time window from Screener chart API
            q_param = urllib.parse.quote("Price to Earning-Median PE-EPS")
            medians = {}
            current_pe_from_chart = None

            for days, key in [(365, "1Y"), (1095, "3Y"), (1825, "5Y")]:
                consolidated_param = "&consolidated=true" if is_consolidated else ""
                chart_url = (
                    f"https://www.screener.in/api/company/{company_id}/chart/"
                    f"?q={q_param}&days={days}{consolidated_param}"
                )
                try:
                    chart_resp = requests.get(chart_url, headers={
                        **self.headers,
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json, */*",
                        "Referer": f"https://www.screener.in/company/{stock}/",
                    }, timeout=6)

                    if chart_resp.status_code != 200:
                        continue

                    chart_data = chart_resp.json()
                    datasets = chart_data.get("datasets", [])

                    for ds in datasets:
                        metric = ds.get("metric", "").lower()
                        label = ds.get("label", "").lower()
                        values = ds.get("values", [])

                        # Extract the Median PE flat line value
                        if "median" in metric or "median" in label:
                            if values:
                                try:
                                    medians[key] = round(float(values[0][1]), 2)
                                except (ValueError, TypeError, IndexError):
                                    pass

                        # Extract the most recent actual PE (only need to do this once)
                        if current_pe_from_chart is None and "price to earning" in metric and values:
                            try:
                                current_pe_from_chart = round(float(values[-1][1]), 2)
                            except (ValueError, TypeError, IndexError):
                                pass

                except Exception:
                    continue

            result["peMedian1Y"] = medians.get("1Y")
            result["peMedian3Y"] = medians.get("3Y")
            result["peMedian5Y"] = medians.get("5Y")

            # Use Screener's actual current PE for comparison (more accurate TTM-based)
            compare_pe = current_pe_from_chart
            if compare_pe is None:
                # Fall back to whatever screener/yfinance returned in the main result
                compare_pe = None

            if compare_pe is not None:
                result["belowMedian1Y"] = bool(compare_pe < medians["1Y"]) if medians.get("1Y") else None
                result["belowMedian3Y"] = bool(compare_pe < medians["3Y"]) if medians.get("3Y") else None
                result["belowMedian5Y"] = bool(compare_pe < medians["5Y"]) if medians.get("5Y") else None

        except Exception as e:
            print(f"Error fetching PE medians from Screener for {stock}: {e}")

        return result