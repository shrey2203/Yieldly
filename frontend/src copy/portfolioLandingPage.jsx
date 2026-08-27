import React, { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { AllCommunityModule, ModuleRegistry, ClientSideRowModelModule } from "ag-grid-community";
import PortfolioUI from "./portfolioUI"; 
import "./Portfolio.css";

ModuleRegistry.registerModules([ClientSideRowModelModule, AllCommunityModule]);

const Portfolio = () => {
    const [portfolioData, setPortfolioData] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [refresh, setRefresh] = useState(false); 
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split("T")[0]);
    const [tempDate, setTempDate] = useState(selectedDate);
    const userId = localStorage.getItem("username");
    const gridRef = useRef(); 
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedRowData, setSelectedRowData] = useState(null);
    const onRowDoubleClicked = useCallback((params) => {setSelectedRowData(params.data); setModalOpen(true);}, []);
    const [activeTab, setActiveTab] = useState('transactions');
    const [scripHistory, setScripHistory] = useState([]);
    const [isHistoryLoading, setIsHistoryLoading] = useState(false);
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
                {
                    headers: { 'Authorization': `Bearer ${token}` }
                }
            );
            
            if (!response.ok) throw new Error("Network response was not ok");
            
            const data = await response.json();
            
            // Ensure data is mapped to keys Recharts expects
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

    // --- Helpers ---
    const formatINR = (num) => Number(num || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });

    // --- Aggregation Functions ---
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

    // --- Fetch Data ---
    const fetchData = async () => {
        setLoading(true);
        try {
            const [portRes, chartRes] = await Promise.all([
                fetch(`api/fetchPortfolio?userId=${userId}&selectedDate=${selectedDate}`, {
                    headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
                }),
                fetch(`api/fetchChartData?userId=${userId}&selectedDate=${selectedDate}`)
            ]);
            
            const pData = await portRes.json();
            const cData = await chartRes.json();

            // 1. Filter out TOTAL row
            const cleanData = pData.filter(item => 
                item.stock !== "TOTAL" && 
                item.stock !== "TOTAL: " && 
                !String(item.stock).startsWith("TOTAL")
            );

            // 2. Calculate Portfolio Total Value
            const totalPortfolioValue = cleanData.reduce((sum, item) => sum + (Number(item.totalValue) || 0), 0);

            // 3. Add 'portfolioWeight' to each stock
            const dataWithWeights = cleanData.map(item => ({
                ...item,
                portfolioWeight: totalPortfolioValue ? ((item.totalValue / totalPortfolioValue) * 100) : 0
            }));

            setPortfolioData(dataWithWeights);
            
            if (cData && cData[0]) {
                setChartData(cData[0].map((date, i) => ({
                    date: date,
                    value: cData[1][i],
                    invested: cData[2][i]
                })));
            }
        } catch (err) {
            console.error(err);
            setError("Connectivity issue. Please try again later.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, [userId, selectedDate]);

    const dateFormatter = (params) => {
        if (!params.value) return params.colDef.field === 'sellDate' ? "—" : "";
        const date = new Date(params.value);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}-${month}-${year}`;
    };

    // --- Sector Breakdown ---
    const sectorData = useMemo(() => {
        const sectors = {};
        portfolioData.forEach(item => {
            const sec = item.sector || item.industry || "Unknown";
            sectors[sec] = (sectors[sec] || 0) + (Number(item.totalValue) || 0);
        });
        return Object.entries(sectors)
            .map(([name, value]) => ({ name, value }))
            .filter(item => item.value > 0);
    }, [portfolioData]);

    // --- Summary Metrics ---
    const summary = useMemo(() => {
        const invested = portfolioData.reduce((s, r) => s + (Number(r.totalBuy) || 0), 0);
        const current = portfolioData.reduce((s, r) => s + (Number(r.totalValue) || 0), 0);
        const today = portfolioData.reduce((s, r) => s + (Number(r.dailyChange) || 0), 0);
        return {
            invested, current, pnl: current - invested,
            pnlPct: invested ? ((current - invested) * 100) / invested : 0,
            today, todayPct: current ? (today * 100) / current : 0
        };
    }, [portfolioData]);

    // --- Compact Column Definitions ---
    const columnDefs = useMemo(() => [
        { 
            field: "stock", headerName: "Scrip", sort: "asc",
            flex: 1.2, minWidth: 120, pinned: 'left' 
        },
        { 
            field: "quantity", headerName: "Qty", 
            flex: 0.9, width: 70, minWidth: 60, resizable: false,
            valueFormatter: p => formatINR(p.value) 
        },
        { 
            field: "price", headerName: "Avg", 
            flex: 0.9, width: 80, minWidth: 70, 
            valueFormatter: p => formatINR(p.value) 
        },
        { 
            field: "totalBuy", headerName: "Invested", 
            flex: 1, minWidth: 100, 
            valueFormatter: p => "₹" + formatINR(p.value), aggFunc: 'sum' 
        },
        { 
            field: "portfolioWeight", headerName: "Wt %", 
            flex: 0.9, width: 75, minWidth: 60,
            valueFormatter: p => p.value ? Number(p.value).toFixed(1) + "%" : "0.0%",
            cellStyle: { fontWeight: 'bold', color: '#94a3b8' } // Grey color for subtle look
        },
        { 
            field: "ltp", headerName: "LTP", 
            flex: 0.9, width: 70, minWidth: 70, cellClass: "ltp-highlight", 
            valueFormatter: p => formatINR(p.value) 
        },
        { 
            field: "totalValue", headerName: "Current", 
            flex: 1, minWidth: 100, 
            valueFormatter: p => "₹" + formatINR(p.value), aggFunc: 'sum' 
        },
        { 
            field: "unrealisedPnL", headerName: "P&L", 
            flex: 0.9, minWidth: 90,
            cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" }, 
            valueFormatter: p => formatINR(p.value), aggFunc: 'sum'
        },
        { 
            field: "pnlPercent", headerName: "P&L %", 
            flex: 0.9, width: 85, minWidth: 70,
            valueFormatter: p => {
                const val = Number(p.value);
                return isNaN(val) || val === 0 ? "" : val.toFixed(1) + "%"; // Rounded to 1 decimal for space
            },
            cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" }
        },
        { 
            field: "dailyChange", headerName: "Day Chg", 
            flex: 0.9, width: 90, minWidth: 80,
            valueFormatter: p => p.value ? Number(p.value).toFixed(1) : "", // No decimals for day change value
            cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" },
            aggFunc: 'sum'
        },
        { 
            field: "dailyChangePercent", headerName: "Day %", 
            flex: 0.9, width: 85, minWidth: 70,
            cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" }, 
            valueFormatter: p => p.value ? Number(p.value).toFixed(1) + "%" : "0.0%" 
        }
    ], []);

    // Update the transactionColumnDefs to use the dateFormatter
    const transactionColumnDefs = useMemo(() => [
        { 
            field: 'buyDate', 
            headerName: 'Buy Date', 
            flex: 1, 
            sort: 'desc',
            valueFormatter: dateFormatter // Apply dd-mm-yyyy here
        },
        { 
            field: 'sellDate', 
            headerName: 'Sell Date', 
            flex: 1,
            // Combined logic: Format date OR show dash
            valueFormatter: p => p.value ? dateFormatter(p) : "—" 
        },
        { 
            field: 'quantity', 
            headerName: 'Qty', 
            flex: 0.7 
        },
        { 
            field: 'buyPrice', 
            headerName: 'Buy Price', 
            flex: 1,
            valueFormatter: p => formatINR(p.value)
        },
        { 
            field: 'sellPrice', 
            headerName: 'Sell Price/ LTP', 
            flex: 1,
            valueFormatter: p => p.value ? formatINR(p.value) : "Holding"
        },
        { 
            field: 'status', 
            headerName: 'Status', 
            flex: 0.8,
            cellClassRules: {
                'text-green': "x === 'Open'",
                'text-amber': "x === 'Closed'"
            }
        },
        { 
            field: 'pnl', 
            headerName: 'Realised/ Unrealised P&L', 
            flex: 1,
            valueFormatter: p => p.value ? "₹" + formatINR(p.value) : "₹0",
            cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" }
        },
        { 
            headerName: 'P&L %', 
            flex: 0.8,
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
            cellStyle: { textAlign: 'center', fontWeight: 'bold' }
        },
        { 
            field: 'holdingDays', 
            headerName: 'Days', 
            flex: 0.6,
            valueFormatter: p => `${p.value} d`,
            cellStyle: { color: '#94a3b8', textAlign: 'center' } 
        }        
    ], [formatINR]); 

    return (
        <PortfolioUI 
            gridRef={gridRef} portfolioData={portfolioData} chartData={chartData}
            sectorData={sectorData} summary={summary} columnDefs={columnDefs}
            loading={loading} refresh={refresh} setRefresh={setRefresh}
            tempDate={tempDate} setTempDate={setTempDate} setSelectedDate={setSelectedDate}
            formatINR={formatINR}
            onRowDoubleClicked={onRowDoubleClicked}
            modalOpen={modalOpen} setModalOpen={setModalOpen} selectedRowData={selectedRowData} transactionColumnDefs ={transactionColumnDefs}
            activeTab = {activeTab} setActiveTab = {setActiveTab} scripHistory={scripHistory} isHistoryLoading={isHistoryLoading} fetchScripPerformance={fetchScripPerformance}
        />
    );
};

export default Portfolio;