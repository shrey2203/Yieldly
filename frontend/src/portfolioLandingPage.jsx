import React, { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { AllCommunityModule, ModuleRegistry, ClientSideRowModelModule } from "ag-grid-community";
import PortfolioUI from "./portfolioUI"; 
import "./Portfolio.css";

ModuleRegistry.registerModules([ClientSideRowModelModule, AllCommunityModule]);

const Portfolio = () => {
    const [searchParams] = useSearchParams();
    const tabParam = searchParams.get('tab');
    const [portfolioData, setPortfolioData] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [refresh, setRefresh] = useState(false); 
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split("T")[0]);
    const [tempDate, setTempDate] = useState(selectedDate);
    const rawUser = localStorage.getItem("username");
    const userId = (rawUser && rawUser !== "null" && rawUser !== "undefined") ? rawUser : "SHREY";
    const gridRef = useRef(); 
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedRowData, setSelectedRowData] = useState(null);
    const [viewTab, setViewTab] = useState(tabParam === 'dividends' ? 'dividends' : 'holdings'); 
    const [activeTab, setActiveTab] = useState('transactions');
    const [scripHistory, setScripHistory] = useState([]);
    const [isHistoryLoading, setIsHistoryLoading] = useState(false);
    const [rawRealisedData, setRawRealisedData] = useState({});
    const [dividendData, setDividendData] = useState([]);
    const [totalDividends, setTotalDividends] = useState(0);
    const [dividendsList, setDividendsList] = useState([]);

    const fetchTotalDividends = useCallback(async () => {
        const activeUser = (userId && userId !== "null" && userId !== "undefined") ? userId : (localStorage.getItem("username") || "SHREY");
        try {
            const token = localStorage.getItem("token");
            const response = await fetch(
                `/api/fetchTotalDividends?userId=${encodeURIComponent(activeUser)}`, 
                {headers: token ? { 'Authorization': `${token}` } : {}}
            );
            if (!response.ok) throw new Error("Network response was not ok");
            const data = await response.json();
            setTotalDividends(data.totalDividends || 0);
            setDividendsList(data.dividendsList || []);
        } catch (err) {
            console.error("Error fetching total dividends:", err);
            setTotalDividends(0);
            setDividendsList([]);
        }
    }, [userId]);

    useEffect(() => {
        if (tabParam === 'dividends') {
            setViewTab('dividends');
            fetchTotalDividends();
        }
    }, [tabParam, fetchTotalDividends]);

    useEffect(() => {
        if (viewTab === 'dividends' && dividendsList.length === 0) {
            fetchTotalDividends();
        }
    }, [viewTab, dividendsList.length, fetchTotalDividends]);

    useEffect(() => {
        setScripHistory([]);
        setActiveTab('transactions'); // Reset to first tab on close
    }, [modalOpen]);

    const fetchScripPerformance = useCallback(async (symbol) => {
        if (!symbol) return;
        
        setIsHistoryLoading(true);
        try {
            const token = localStorage.getItem("token");
            const response = await fetch(
                `/api/fetchScripHistory?userId=${userId}&symbol=${encodeURIComponent(symbol)}`, 
                {headers: { 'Authorization': `Bearer ${token}` }}
            );
            if (!response.ok) throw new Error("Network response was not ok");
            const data = await response.json();
            const formattedData = data.map(item => ({
                date: item.date,
                price: Number(item.price),
                ema20: item.ema20,   // MUST include these
                ema50: item.ema50,
                ema100: item.ema100,
                ema200: item.ema200
            }));
    
            setScripHistory(formattedData);
        } catch (err) {
            console.error("Error fetching scrip history:", err);
        } finally {
            setIsHistoryLoading(false);
        }
    }, [userId]);

    const fetchScripDividends = useCallback(async (symbol) => {
        if (!symbol) return;
        
        try {
            const token = localStorage.getItem("token");
            const response = await fetch(
                `/api/fetchScripDividends?userId=${userId}&symbol=${encodeURIComponent(symbol)}`, 
                {headers: { 'Authorization': `${token}` }}
            );
            if (!response.ok) throw new Error("Network response was not ok");
            const data = await response.json();
            setDividendData(data || []);
        } catch (err) {
            console.error("Error fetching dividends:", err);
            setDividendData([]);
        }
    }, [userId]);

    // --- Helpers ---
    const formatINR = (num) => Number(num || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });

    const onRowDoubleClicked = useCallback((params) => {
        let dataToDisplay = { ...params.data };

        // Scenario A: Clicked from Realised Tab (Summary Row)
        if (viewTab === 'realised') {
            // 1. Find the raw trade list from the state we populated via API
            const rawTrades = rawRealisedData[params.data.stock] || [];
            
            // 2. Format these raw trades to match your transactionColumnDefs
            const formattedSummary = rawTrades.map(t => ({
                buyDate: t.buyDate,
                sellDate: t.sellDate,
                quantity: t.qty,
                buyPrice: t.buyPrice,
                sellPrice: t.sellPrice,
                pnl: t.pnl,
                status: 'Closed',
                holdingDays: t.buyDate && t.sellDate ? 
                    Math.floor((new Date(t.sellDate) - new Date(t.buyDate)) / (1000 * 60 * 60 * 24)) : 0,
                niftyLevelAtBuy: t.niftyLevelAtBuy, 
                niftyLevelAtSell: t.niftyLevelAtSell,
                niftyReturns: t.niftyReturns,
                alphaGenerated: t.alphaGenerated,
                alphaGeneratedPerDay: t.alphaGeneratedPerDay
            }));

            // 3. Attach it so the Modal can find it
            dataToDisplay.transactionSummary = formattedSummary;
            
            // 4. Try to find extra info (sector, etc.) from active holdings if it exists
            const activeInfo = portfolioData.find(item => item.stock === params.data.stock);
            if (activeInfo) {
                dataToDisplay = { ...activeInfo, ...dataToDisplay };
            }
        } 
        // Scenario B: Clicked from Holdings / IPO Tab
        else {
            if (!dataToDisplay.transactionSummary || dataToDisplay.transactionSummary.length === 0) {
                const fullScripData = portfolioData.find(item => item.stock === params.data.stock);
                if (fullScripData && fullScripData.transactionSummary) {
                    dataToDisplay = { ...fullScripData, ...dataToDisplay };
                }
            }
        }

        if (dataToDisplay.transactionSummary && Array.isArray(dataToDisplay.transactionSummary)) {
            dataToDisplay.transactionSummary = [...dataToDisplay.transactionSummary].sort((a, b) => {
                const timeA = new Date(a.buyDate).getTime();
                const timeB = new Date(b.buyDate).getTime();
                return (isNaN(timeA) ? 0 : timeA) - (isNaN(timeB) ? 0 : timeB);
            });
        }

        setSelectedRowData(dataToDisplay); 
        setModalOpen(true);
    }, [portfolioData, rawRealisedData, viewTab]);

    const calculatePnLPercent = useCallback((params) => {
        if (!params || !params.data) return "0";
        let totalValueSum = 0;
        let currentValueSum = 0;
        const rows = params.data || []; 
        rows.forEach(row => {
            totalValueSum += Number(row.totalBuy) || 0;
            currentValueSum += Number(row.totalValue) || 0;
        });
        return totalValueSum !== 0
            ? (((currentValueSum - totalValueSum) / totalValueSum) * 100).toFixed(2)
            : "0";
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("token");
            const [portRes, chartRes] = await Promise.all([
                fetch(`api/fetchPortfolio?userId=${userId}&selectedDate=${selectedDate}`, {
                    headers: { Authorization: `Bearer ${token}` }
                }),
                fetch(`api/fetchChartData?userId=${userId}&selectedDate=${selectedDate}`)
            ]);
    
            if (!portRes.ok || !chartRes.ok) throw new Error("Failed to fetch data");
    
            // Consuming the streams ONLY ONCE
            const pDataResponse = await portRes.json();
            const cData = await chartRes.json();
    
            const rawHoldings = pDataResponse.holdings || [];
            const realisedMap = pDataResponse.realisedSummary || {};
    
            const cleanData = rawHoldings.filter(item => 
                item.stock !== "TOTAL" && !String(item.stock).startsWith("TOTAL")
            );
    
            const activeData = cleanData.filter(item => Number(item.quantity) > 0);
            const totalBuy = activeData.reduce((sum, item) => sum + (Number(item.totalBuy) || 0), 0);
            const totalValue = activeData.reduce((sum, item) => sum + (Number(item.totalValue) || 0), 0);
    
            // Update Holdings
            setPortfolioData(cleanData.map(item => ({
                ...item,
                portfolioWeight: totalValue && Number(item.quantity) > 0 ? ((Number(item.totalValue) / totalValue) * 100) : 0
            })));
    
            // Update Realised Summary (This was crashing before)
            setRawRealisedData(pDataResponse.realisedSummary || {});
    
            // Update Chart
            if (cData && Array.isArray(cData[0])) {
                const mappedChart = cData[0].map((date, i) => ({
                    date: date,
                    invested: Number(cData[1][i]) || 0, // yLabel1 from backend is invested
                    value: Number(cData[2][i]) || 0     // yLabel2 from backend is current value
                }));

                // Ensure the final data point matches the active portfolio totals
                if (mappedChart.length > 0 && totalBuy > 0 && totalValue > 0) {
                    mappedChart[mappedChart.length - 1].invested = totalBuy;
                    mappedChart[mappedChart.length - 1].value = totalValue;
                }

                setChartData(mappedChart);
            }
        } catch (error) {
            console.error("Failed to load portfolio dashboard data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (userId) {
            fetchData();
        }
        fetchTotalDividends();
    }, [userId, selectedDate]);

    // Format dates to DD-MM-YYYY
    const formatDate = (dateStr) => {
        if (!dateStr) return "-";
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        return `${day}-${month}-${year}`;
    };

    const dateFormatter = (params) => {
        if (!params || !params.value) return params?.colDef?.field === 'sellDate' ? "—" : "";
        const date = new Date(params.value);
        if (isNaN(date.getTime())) return String(params.value);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}-${month}-${year}`;
    };

    const dateComparator = (date1, date2) => {
        if (!date1 && !date2) return 0;
        if (!date1) return -1;
        if (!date2) return 1;
        const time1 = new Date(date1).getTime();
        const time2 = new Date(date2).getTime();
        if (isNaN(time1) || isNaN(time2)) return 0;
        return time1 - time2;
    };

    // --- Sector Breakdown ---
    const sectorData = useMemo(() => {
        const sectors = {};
        portfolioData.filter(item => Number(item.quantity) > 0).forEach(item => {
            const sec = item.sector || item.industry || "Unknown";
            sectors[sec] = (sectors[sec] || 0) + (Number(item.totalValue) || 0);
        });
        return Object.entries(sectors)
            .map(([name, value]) => ({ name, value }))
            .filter(item => item.value > 0);
    }, [portfolioData]);

    const summary = useMemo(() => {
        // Standard Holdings logic (only active positions)
        const activeHoldings = portfolioData.filter(r => Number(r.quantity) > 0);
        const invested = activeHoldings.reduce((s, r) => s + (Number(r.totalBuy) || 0), 0);
        const current = activeHoldings.reduce((s, r) => s + (Number(r.totalValue) || 0), 0);
        const today = activeHoldings.reduce((s, r) => s + (Number(r.dailyChange) || 0), 0);
    
        // FIX: Use 'rawRealisedData' (the state) NOT 'summary.realisedSummary'
        let totalGains = 0;
        let totalLosses = 0;
        const processedRealised = {};
    
        Object.entries(rawRealisedData).forEach(([ticker, trades]) => {
            // Since you're sending raw trades now, each 'trades' is an array of objects
            const netPnL = trades.reduce((sum, t) => sum + (Number(t.pnl) || 0), 0);
            
            // Filter noise (±500)
            if (Math.abs(netPnL) > 500) {
                processedRealised[ticker] = netPnL;
                if (netPnL > 0) totalGains += netPnL;
                else totalLosses += netPnL;
            }
        });
    
        return {
            invested,
            current,
            pnl: current - invested,
            pnlPct: invested ? ((current - invested) * 100) / invested : 0,
            today,
            todayPct: current ? (today * 100) / current : 0,
            
            // Realised Metrics
            realisedGains: totalGains,
            realisedLosses: totalLosses,
            totalRealised: totalGains + totalLosses,
            displayRealisedMap: processedRealised,
            rawRealisedData: rawRealisedData, // Keep the raw trades for modal attribution
            totalDividends: totalDividends,
            dividendsList: dividendsList
        };
    }, [portfolioData, rawRealisedData, totalDividends, dividendsList]); // Depend on the raw state

    // --- Master Equity Column Definitions ---
    const ALL_EQUITY_COLUMNS = useMemo(() => [
        { id: "stock", field: "stock", headerName: "Scrip", sort: "asc", flex: 1.2, minWidth: 120, pinned: 'left', defaultVisible: true },
        { id: "quantity", field: "quantity", headerName: "Qty", flex: 0.9, width: 70, minWidth: 60, resizable: false, valueFormatter: p => formatINR(p.value), defaultVisible: true },
        { id: "price", field: "price", headerName: "Avg", flex: 0.9, width: 80, minWidth: 70, cellClass: "avg-highlight", valueFormatter: p => formatINR(p.value), defaultVisible: true },
        { id: "totalBuy", field: "totalBuy", headerName: "Invested", flex: 1, minWidth: 100, valueFormatter: p => "₹" + formatINR(p.value), aggFunc: 'sum', defaultVisible: true },
        { 
            id: "portfolioWeight",
            field: "portfolioWeight", 
            headerName: "Wt %", 
            flex: 1, minWidth: 100,
            defaultVisible: true,
            cellRenderer: (params) => {
                if (!params.value) return "0.0%";
                const pct = Number(params.value).toFixed(1);
                return (
                    <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
                        <span style={{ width: '40px' }}>{pct}%</span>
                        <div style={{ flex: 1, height: '6px', background: '#e2e8f0', borderRadius: '3px', marginLeft: '8px' }}>
                            <div style={{ width: `${pct}%`, height: '100%', background: '#3b82f6', borderRadius: '3px' }}></div>
                        </div>
                    </div>
                );
            }
        },
        { id: "ltp", field: "ltp", headerName: "LTP", flex: 0.9, width: 70, minWidth: 70, cellClass: "ltp-highlight", valueFormatter: p => formatINR(p.value), defaultVisible: true },
        { id: "totalValue", field: "totalValue", headerName: "Current", flex: 1, minWidth: 100, valueFormatter: p => "₹" + formatINR(p.value), aggFunc: 'sum', defaultVisible: true },
        { 
            id: "unrealisedPnL",
            field: "unrealisedPnL", headerName: "P&L", 
            flex: 0.9, minWidth: 90,
            cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" }, 
            valueFormatter: p => formatINR(p.value), aggFunc: 'sum',
            defaultVisible: true
        },
        { 
            id: "pnlPercent",
            field: "pnlPercent", headerName: "P&L %", 
            flex: 0.9, width: 85, minWidth: 70,
            valueFormatter: p => {
                const val = Number(p.value);
                return isNaN(val) || val === 0 ? "" : val.toFixed(1) + "%";
            },
            cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" },
            defaultVisible: true
        },
        { 
            id: "dailyChange",
            field: "dailyChange", headerName: "Day Chg", 
            flex: 0.9, width: 90, minWidth: 80,
            valueFormatter: p => p.value ? Number(p.value).toFixed(1) : "",
            cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" },
            aggFunc: 'sum',
            defaultVisible: true
        },
        { 
            id: "dailyChangePercent",
            field: "dailyChangePercent", headerName: "Day %", 
            flex: 0.9, width: 85, minWidth: 70,
            cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" }, 
            valueFormatter: p => p.value ? Number(p.value).toFixed(1) + "%" : "0.0%",
            defaultVisible: true
        },
        { id: "sector", field: "sector", headerName: "Sector", flex: 1, minWidth: 110, defaultVisible: false },
        { id: "industry", field: "industry", headerName: "Industry", flex: 1, minWidth: 110, defaultVisible: false },
        { id: "peRatio", field: "peRatio", headerName: "P/E", flex: 0.8, minWidth: 75, valueFormatter: p => p.value ? Number(p.value).toFixed(1) : "-", defaultVisible: false },
        { id: "yearHigh", field: "yearHigh", headerName: "52W High", flex: 0.9, minWidth: 85, valueFormatter: p => p.value ? "₹" + formatINR(p.value) : "-", defaultVisible: false },
        { id: "yearLow", field: "yearLow", headerName: "52W Low", flex: 0.9, minWidth: 85, valueFormatter: p => p.value ? "₹" + formatINR(p.value) : "-", defaultVisible: false },
        { id: "category", field: "category", headerName: "Category", flex: 0.9, minWidth: 90, defaultVisible: false }
    ], []);

    // Column visibility preferences
    const [visibleCols, setVisibleCols] = useState(() => {
        const saved = localStorage.getItem("equity_visible_columns");
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                console.error("Error parsing saved columns", e);
            }
        }
        return {
            stock: true,
            quantity: true,
            price: true,
            totalBuy: true,
            portfolioWeight: true,
            ltp: true,
            totalValue: true,
            unrealisedPnL: true,
            pnlPercent: true,
            dailyChange: true,
            dailyChangePercent: true,
            sector: false,
            industry: false,
            peRatio: false,
            yearHigh: false,
            yearLow: false,
            category: false
        };
    });

    const columnDefs = useMemo(() => {
        return ALL_EQUITY_COLUMNS.filter(col => visibleCols[col.id]);
    }, [ALL_EQUITY_COLUMNS, visibleCols]);

    // Update the transactionColumnDefs to use the dateFormatter
    const transactionColumnDefs = useMemo(() => [
        { 
            field: 'buyDate', 
            headerName: 'Buy Date', 
            sort: 'asc',
            comparator: dateComparator,
            filter: 'agDateColumnFilter',
            valueFormatter: dateFormatter // Apply dd-mm-yyyy here
        },
        { 
            field: 'sellDate', 
            headerName: 'Sell Date', 
            comparator: dateComparator,
            filter: 'agDateColumnFilter',
            valueFormatter: p => p.value ? dateFormatter(p) : "—" 
        },
        { 
            field: 'quantity', 
            headerName: 'Qty', 
            // flex: 1
        },
        { 
            field: 'buyPrice', 
            headerName: 'Buy Price', 
            // flex: 1,
            valueFormatter: p => formatINR(p.value)
        },
        { 
            headerName: 'Total Invested', 
            // flex: 1,
            valueGetter: (params) => {
                const { pnl, quantity, buyPrice } = params.data;
                return formatINR(quantity * buyPrice);
            }
        },
        { 
            field: 'sellPrice', 
            headerName: 'Sell Price/ LTP', 
            // flex: 1,
            valueFormatter: p => p.value ? formatINR(p.value) : "Holding"
        },
        { 
            headerName: 'Total Current/ Sell Value', 
            // flex: 1,
            valueGetter: (params) => {
                const { quantity, sellPrice, buyPrice } = params.data;
                // Use sellPrice (LTP) if available, otherwise fall back to buyPrice or 0
                const currentPrice = sellPrice || buyPrice || 0;
                return formatINR(quantity * currentPrice);
            }
        },
        { 
            field: 'status', 
            headerName: 'Status', 
            // flex: 1,
            cellClassRules: {
                'text-green': "x === 'Open'",
                'text-amber': "x === 'Closed'"
            }
        },
        { 
            field: 'pnl', 
            headerName: 'Realised/ Unrealised P&L', 
            // flex: 1,
            valueFormatter: p => p.value ? "₹" + formatINR(p.value) : "₹0",
            cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" }
        },
        { 
            headerName: 'P&L %', 
            // flex: 1,
            valueGetter: params => {
                const { pnl, quantity, buyPrice } = params.data;
                const totalCost = quantity * buyPrice;
                if (!totalCost || totalCost === 0) return 0;
                return (pnl / totalCost) * 100;
            },
            valueFormatter: p => {
                const val = Number(p.value);
                return (val >= 0 ? "+" : "") + val.toFixed(2) + "%";
            },
            cellClassRules: {
                'text-green': "x > 0",
                'text-red': "x < 0"
            },
            cellStyle: {fontWeight: 'bold' }
        },
        { 
            field: 'holdingDays', 
            headerName: 'Days', 
            // flex: 1,
            valueFormatter: p => `${p.value} d`,
            cellStyle: { color: '#94a3b8'} 
        },
        { 
            field: 'niftyLevelAtBuy', 
            headerName: 'Nifty Level Buy', 
            valueFormatter: p => p.value ? Number(p.value).toLocaleString('en-IN') : '-'
        },
        { 
            field: 'niftyLevelAtSell', 
            headerName: 'Nifty Level Sell/ Current', 
            valueFormatter: p => p.value ? Number(p.value).toLocaleString('en-IN') : '-'
        },
        { 
            field: 'niftyReturns',
            headerName: 'Nifty Returns %', 
            valueFormatter: p => {
                if (p.value == null) return '-';
                const val = Number(p.value);
                return (val >= 0 ? "+" : "") + val.toFixed(2) + "%";
            },
            cellClassRules: {
                'text-green': "x > 0",
                'text-red': "x < 0"
            }
        },
        { 
            field: 'alphaGenerated',
            headerName: 'Alpha Generated', 
            valueFormatter: p => {
                const val = Number(p.value);
                return (val >= 0 ? "+" : "") + val.toFixed(2) + "%";
            },
            cellClassRules: {
                'text-green': "x > 0",
                'text-red': "x < 0"
            },
            cellStyle: { fontWeight: 'bold' }
        },
        { 
            field: 'alphaGeneratedPerDay',
            headerName: 'Alpha Generated per Day', 
            valueFormatter: p => {
                const val = Number(p.value);
                return (val >= 0 ? "+" : "") + val.toFixed(4) + "%";
            },
            cellClassRules: {
                'text-green': "x > 0",
                'text-red': "x < 0"
            },
            cellStyle: { fontWeight: 'bold' }
        },
        { 
            headerName: 'Tax Category', 
            valueGetter: params => {
                const days = params.data.holdingDays;
                if (!days) return "—";
                return days >= 365 ? "LTCG" : "STCG";
            },
            cellClassRules: {
                'text-blue-600': "x === 'LTCG'",
                'text-orange-500': "x === 'STCG'"
            }
        }
    ], [formatINR]); 

    return (
        <PortfolioUI 
            gridRef={gridRef} portfolioData={portfolioData} chartData={chartData}
            sectorData={sectorData} summary={summary} columnDefs={columnDefs}
            ALL_EQUITY_COLUMNS={ALL_EQUITY_COLUMNS} visibleCols={visibleCols} setVisibleCols={setVisibleCols}
            loading={loading} refresh={refresh} setRefresh={setRefresh}
            tempDate={tempDate} setTempDate={setTempDate} setSelectedDate={setSelectedDate}
            formatINR={formatINR} viewTab={viewTab} setViewTab={setViewTab}
            onRowDoubleClicked={onRowDoubleClicked}
            modalOpen={modalOpen} setModalOpen={setModalOpen} selectedRowData={selectedRowData} transactionColumnDefs ={transactionColumnDefs}
            activeTab = {activeTab} setActiveTab = {setActiveTab} scripHistory={scripHistory} isHistoryLoading={isHistoryLoading} fetchScripPerformance={fetchScripPerformance} fetchScripDividends={fetchScripDividends} dividendData={dividendData} rawRealisedData ={rawRealisedData}
            fetchTotalDividends={fetchTotalDividends}
        />
    );
};

export default Portfolio;