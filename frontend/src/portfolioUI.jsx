import React, { useState, useMemo, useEffect, useRef } from "react";
import { AgGridReact } from "ag-grid-react";
import { 
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend, Line, ReferenceArea
} from "recharts";

// Expanded color palette to handle more sectors if needed
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#6366f1', '#a855f7', '#14b8a6'];

const PortfolioUI = ({
    gridRef, portfolioData, chartData, sectorData, summary, columnDefs, 
    ALL_EQUITY_COLUMNS = [], visibleCols = {}, setVisibleCols,
    loading, refresh, setRefresh, tempDate, setTempDate, setSelectedDate, formatINR, viewTab, setViewTab, onRowDoubleClicked, modalOpen, setModalOpen, selectedRowData, transactionColumnDefs, activeTab, setActiveTab,
    scripHistory, isHistoryLoading, fetchScripPerformance, fetchScripDividends, dividendData, rawRealisedData, fetchTotalDividends
}) => {
    const [chartType, setChartType] = useState('sector'); 
    const [showColPicker, setShowColPicker] = useState(false);
    const [colSearchQuery, setColSearchQuery] = useState("");
    const [quickFilterText, setQuickFilterText] = useState("");
    const colPickerRef = useRef(null);

    // Toggle single column
    const toggleColumn = (colId) => {
        if (typeof setVisibleCols === "function") {
            setVisibleCols(prev => {
                const updated = { ...prev, [colId]: !prev[colId] };
                localStorage.setItem("equity_visible_columns", JSON.stringify(updated));
                return updated;
            });
        }
    };

    // Bulk selection helpers
    const selectAllColumns = () => {
        if (typeof setVisibleCols === "function") {
            const all = {};
            ALL_EQUITY_COLUMNS.forEach(col => { all[col.id] = true; });
            setVisibleCols(all);
            localStorage.setItem("equity_visible_columns", JSON.stringify(all));
        }
    };

    const deselectAllColumns = () => {
        if (typeof setVisibleCols === "function") {
            const none = { stock: true }; // Keep Scrip always visible
            ALL_EQUITY_COLUMNS.forEach(col => { if (col.id !== "stock") none[col.id] = false; });
            setVisibleCols(none);
            localStorage.setItem("equity_visible_columns", JSON.stringify(none));
        }
    };

    const resetDefaultColumns = () => {
        if (typeof setVisibleCols === "function") {
            const defaults = {};
            ALL_EQUITY_COLUMNS.forEach(col => { defaults[col.id] = col.defaultVisible; });
            setVisibleCols(defaults);
            localStorage.setItem("equity_visible_columns", JSON.stringify(defaults));
        }
    };

    // Close column picker on outside click
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (colPickerRef.current && !colPickerRef.current.contains(e.target)) {
                setShowColPicker(false);
            }
        };
        if (showColPicker) {
            document.addEventListener("mousedown", handleClickOutside);
        }
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [showColPicker]);

    const stockAllocationData = useMemo(() => {
        if (!portfolioData || portfolioData.length === 0) return [];
        const sorted = [...portfolioData].sort((a, b) => Number(b.totalValue) - Number(a.totalValue));
        const top5 = sorted.slice(0, 10).map(item => ({
            name: item.stock,
            value: Number(item.totalValue)
        }));
    const othersValue = sorted.slice(10).reduce((sum, item) => sum + Number(item.totalValue), 0);
    if (othersValue > 0) {
        top5.push({ name: "Others", value: othersValue });
        }
        return top5;
    }, [portfolioData]);

    const totalScripDividends = useMemo(() => {
        if (!dividendData || !Array.isArray(dividendData)) return 0;
        return dividendData.reduce((sum, item) => sum + (Number(item.totalDividend) || 0), 0);
    }, [dividendData]);

    const formatCurrency = (val) => {
        const num = Number(val || 0);
        if (num < 0) {
            return `-₹${formatINR(Math.abs(num))}`;
        }
        return `₹${formatINR(num)}`;
    };

    const [allDividendsModalOpen, setAllDividendsModalOpen] = useState(false);
    const [trendTimeframe, setTrendTimeframe] = useState('ALL');

    // Close all open dialogs on Escape key press
    useEffect(() => {
        const handleKeyDown = (event) => {
            if (event.key === "Escape" || event.key === "Esc" || event.keyCode === 27) {
                setModalOpen(false);
                setAllDividendsModalOpen(false);
                setShowColPicker(false);
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [setModalOpen]);

    const allDividendsColumnDefs = useMemo(() => [
        { 
            field: "stock", 
            headerName: "Scrip", 
            flex: 1.1, 
            minWidth: 110, 
            pinned: 'left',
            cellStyle: { fontWeight: 'bold', color: '#38bdf8' }
        },
        { 
            field: "companyName", 
            headerName: "Company Name", 
            flex: 1.8, 
            minWidth: 160 
        },
        { 
            field: "payoutDate", 
            headerName: "Payout Date", 
            flex: 1.1, 
            minWidth: 120,
            sort: 'desc',
            filter: 'agDateColumnFilter',
            valueFormatter: p => {
                if (!p.value) return "—";
                const d = new Date(p.value);
                if (isNaN(d.getTime())) return p.value;
                const day = String(d.getDate()).padStart(2, '0');
                const month = String(d.getMonth() + 1).padStart(2, '0');
                const year = d.getFullYear();
                return `${day}-${month}-${year}`;
            }
        },
        { 
            field: "quantity", 
            headerName: "Shares Held", 
            flex: 1, 
            minWidth: 100, 
            valueFormatter: p => formatINR(p.value) 
        },
        { 
            field: "dividendPerShare", 
            headerName: "Dividend / Share", 
            flex: 1.1, 
            minWidth: 120, 
            valueFormatter: p => "₹" + formatINR(p.value) 
        },
        { 
            field: "amount", 
            headerName: "Total Payout", 
            flex: 1.2, 
            minWidth: 120, 
            valueFormatter: p => "₹" + formatINR(p.value),
            cellClassRules: { 'text-green': "x > 0" },
            cellStyle: { fontWeight: 'bold' }
        }
    ], [formatINR]);

    const filteredTrendData = useMemo(() => {
        if (!chartData || chartData.length === 0) return [];
        if (trendTimeframe === 'ALL') return chartData;

        const latestDate = new Date(chartData[chartData.length - 1].date);
        let daysToSubtract = 30;
        if (trendTimeframe === '1M') daysToSubtract = 30;
        else if (trendTimeframe === '3M') daysToSubtract = 90;
        else if (trendTimeframe === '6M') daysToSubtract = 180;
        else if (trendTimeframe === '1Y') daysToSubtract = 365;

        const cutoffDate = new Date(latestDate);
        cutoffDate.setDate(cutoffDate.getDate() - daysToSubtract);

        const filtered = chartData.filter(d => new Date(d.date) >= cutoffDate);
        return filtered.length > 0 ? filtered : chartData;
    }, [chartData, trendTimeframe]);

    const trendStats = useMemo(() => {
        if (!filteredTrendData || filteredTrendData.length < 2) return null;
        const start = filteredTrendData[0];
        const end = filteredTrendData[filteredTrendData.length - 1];
        const startVal = Number(start.value) || 0;
        const endVal = Number(end.value) || 0;
        const diff = endVal - startVal;
        const percent = startVal > 0 ? (diff / startVal) * 100 : 0;
        return {
            diff,
            percent,
            currentVal: endVal,
            investedVal: Number(end.invested) || 0,
            isPositive: diff >= 0
        };
    }, [filteredTrendData]);

    const formatCompactINR = (val) => {
        const num = Math.abs(Number(val) || 0);
        const sign = Number(val) < 0 ? "-" : "";
        if (num >= 10000000) {
            return `${sign}₹${(num / 10000000).toFixed(2)}Cr`;
        }
        if (num >= 100000) {
            return `${sign}₹${(num / 100000).toFixed(1)}L`;
        }
        if (num >= 1000) {
            return `${sign}₹${(num / 1000).toFixed(0)}k`;
        }
        return `${sign}₹${num}`;
    };

    const CustomTrendTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            const dataPoint = payload[0]?.payload;
            if (!dataPoint) return null;
            const val = Number(dataPoint.value) || 0;
            const inv = Number(dataPoint.invested) || 0;
            const pnl = val - inv;
            const pnlPct = inv > 0 ? (pnl / inv) * 100 : 0;

            return (
                <div style={{
                    background: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
                    color: '#0f172a',
                    minWidth: '210px',
                    fontSize: '12px'
                }}>
                    <div style={{ color: '#64748b', marginBottom: '8px', borderBottom: '1px solid #f1f5f9', paddingBottom: '4px', fontWeight: 500 }}>
                        📅 {formatTooltipDate(label)}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                        <span style={{ color: '#0284c7', fontWeight: 600 }}>● Current Value:</span>
                        <strong style={{ color: '#0f172a' }}>₹{formatINR(val)}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                        <span style={{ color: '#9333ea', fontWeight: 600 }}>● Invested:</span>
                        <strong style={{ color: '#0f172a' }}>₹{formatINR(inv)}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '5px', borderTop: '1px solid #f1f5f9' }}>
                        <span style={{ color: pnl >= 0 ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                            ● {pnl >= 0 ? 'Gain' : 'Loss'}:
                        </span>
                        <strong style={{ color: pnl >= 0 ? '#10b981' : '#ef4444' }}>
                            {pnl >= 0 ? '+' : ''}₹{formatINR(pnl)} ({pnl >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%)
                        </strong>
                    </div>
                </div>
            );
        }
        return null;
    };

    const { 
        stockRealized, stockUnrealized, 
        realizedSTCG, realizedLTCG, 
        unrealizedSTCG, unrealizedLTCG 
    } = useMemo(() => {
        let realized = 0, unrealized = 0;
        let rSTCG = 0, rLTCG = 0;
        let uSTCG = 0, uLTCG = 0;

        // Use tempDate if filtering historical dates, else use today's date
        const currentDate = tempDate ? new Date(tempDate) : new Date();

        if (selectedRowData?.transactionSummary) {
            selectedRowData.transactionSummary.forEach(trx => {
                const pnl = Number(trx.pnl) || 0;
                
                if (trx.status === 'Closed') {
                    realized += pnl;
                    if (trx.buyDate && trx.sellDate) {
                        const daysHeld = Math.floor((new Date(trx.sellDate) - new Date(trx.buyDate)) / (1000 * 60 * 60 * 24));
                        if (daysHeld >= 365) rLTCG += pnl;
                        else rSTCG += pnl;
                    } else {
                        rSTCG += pnl; // Default to STCG if dates are missing
                    }
                }
                
                if (trx.status === 'Open') {
                    unrealized += pnl;
                    if (trx.buyDate) {
                        const daysHeld = Math.floor((currentDate - new Date(trx.buyDate)) / (1000 * 60 * 60 * 24));
                        if (daysHeld >= 365) uLTCG += pnl;
                        else uSTCG += pnl;
                    } else {
                        uSTCG += pnl;
                    }
                }
            });
        }
        
        return { 
            stockRealized: realized, stockUnrealized: unrealized,
            realizedSTCG: rSTCG, realizedLTCG: rLTCG,
            unrealizedSTCG: uSTCG, unrealizedLTCG: uLTCG
        };
    }, [selectedRowData, tempDate]); // Added tempDate dependency

    const handleTabChange = (tab) => {
        setActiveTab(tab);
        if (tab === 'chart' && (!scripHistory || scripHistory.length === 0)) {
            fetchScripPerformance(selectedRowData?.stock);
        }
        if (tab === 'dividends') {
            fetchScripDividends(selectedRowData?.stock);
        }
    };

    useEffect(() => {
        if (modalOpen && selectedRowData?.stock) {
            fetchScripDividends(selectedRowData.stock);
        }
    }, [modalOpen, selectedRowData?.stock, fetchScripDividends]);

    const [visibleLines, setVisibleLines] = useState({
        ema20: true,
        ema50: true,
        ema100: true,
        ema200: true
    });
    
    const toggleLine = (key) => {
        setVisibleLines(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const [zoomState, setZoomState] = useState({
        refAreaLeft: "",
        refAreaRight: "",
        data: scripHistory,
    });

    useEffect(() => {
        setZoomState((prev) => ({ ...prev, data: scripHistory }));
    }, [scripHistory]);

    const handleZoom = () => {
        let { refAreaLeft, refAreaRight } = zoomState;
        if (refAreaLeft === refAreaRight || refAreaRight === "") {
            setZoomState((prev) => ({ ...prev, refAreaLeft: "", refAreaRight: "" }));
            return;
        }
        if (refAreaLeft > refAreaRight) [refAreaLeft, refAreaRight] = [refAreaRight, refAreaLeft];

        const startIndex = scripHistory.findIndex((d) => d.date === refAreaLeft);
        const endIndex = scripHistory.findIndex((d) => d.date === refAreaRight);

        setZoomState((prev) => ({
            ...prev,
            refAreaLeft: "",
            refAreaRight: "",
            data: scripHistory.slice(startIndex, endIndex + 1),
        }));
    };
    const resetZoom = () => {
        setZoomState((prev) => ({ 
            ...prev, 
            data: scripHistory, 
            refAreaLeft: "", 
            refAreaRight: "" 
        }));
    };

    const filteredRowData = useMemo(() => {
        if (viewTab === 'ipo') {
            return portfolioData.filter(item => 
                item.isIPO === true || 
                String(item.type || '').trim().toUpperCase() === 'IPO' || 
                String(item.TYPE || '').trim().toUpperCase() === 'IPO' ||
                (item.transactionSummary && item.transactionSummary.some(t => String(t.type || t.TYPE || '').trim().toUpperCase() === 'IPO' || t.isIPO))
            );
        }
        
        if (viewTab === 'realised') {
            return Object.entries(summary.displayRealisedMap || {})
                .map(([ticker, pnl]) => ({
                    stock: ticker,
                    realisedPnL: pnl,
                }))
                .filter(item => Math.abs(item.realisedPnL) > 500) 
                .sort((a, b) => b.realisedPnL - a.realisedPnL);
        }
        
        // Active Holdings: only stocks with open positions
        return portfolioData.filter(item => Number(item.quantity) > 0);
    }, [viewTab, portfolioData, summary]);

    // Compute top card metrics dynamically per tab (Holdings vs IPO)
    const activeTabSummary = useMemo(() => {
        // For Active Holdings
        const activeRows = portfolioData.filter(item => Number(item.quantity) > 0);
        const invested = activeRows.reduce((s, r) => s + (Number(r.totalBuy) || 0), 0);
        const current = activeRows.reduce((s, r) => s + (Number(r.totalValue) || 0), 0);
        const today = activeRows.reduce((s, r) => s + (Number(r.dailyChange) || 0), 0);
        const pnl = current - invested;
        const pnlPct = invested ? ((current - invested) * 100) / invested : 0;
        const todayPct = current ? (today * 100) / current : 0;
        return {
            ...summary,
            invested,
            current,
            pnl,
            pnlPct,
            today,
            todayPct
        };
    }, [portfolioData, summary]);

    // Dedicated comprehensive metrics for IPO Corner (Handles both active and closed positions)
    const ipoSummary = useMemo(() => {
        const ipoRows = portfolioData.filter(item => 
            item.isIPO === true || 
            String(item.type || '').trim().toUpperCase() === 'IPO' || 
            String(item.TYPE || '').trim().toUpperCase() === 'IPO' ||
            (item.transactionSummary && item.transactionSummary.some(t => String(t.type || t.TYPE || '').trim().toUpperCase() === 'IPO' || t.isIPO))
        );
        const totalInvested = ipoRows.reduce((s, r) => s + (Number(r.totalInvestedAllTime || r.totalBuy) || 0), 0);
        const activeInvested = ipoRows.filter(r => Number(r.quantity) > 0).reduce((s, r) => s + (Number(r.totalBuy) || 0), 0);
        const closedInvested = ipoRows.filter(r => !r.quantity || Number(r.quantity) <= 0).reduce((s, r) => s + (Number(r.totalInvestedAllTime || r.totalBuy) || 0), 0);
        const totalSold = ipoRows.reduce((s, r) => s + (Number(r.totalSold) || 0), 0);
        const currentHolding = ipoRows.reduce((s, r) => s + (Number(r.totalValue) || 0), 0);
        const realisedPnL = ipoRows.reduce((s, r) => s + (Number(r.realisedPnL) || 0), 0);
        const unrealisedPnL = ipoRows.reduce((s, r) => s + (Number(r.unrealisedPnL) || 0), 0);
        const netPnL = realisedPnL + unrealisedPnL;
        const pnlPct = totalInvested ? ((netPnL * 100) / totalInvested) : 0;
        const activeCount = ipoRows.filter(r => r.status === 'Active' || (Number(r.quantity) > 0 && !r.realisedPnL)).length;
        const partialCount = ipoRows.filter(r => r.status === 'Partially Closed').length;
        const closedCount = ipoRows.filter(r => r.status === 'Closed' || Number(r.quantity) === 0).length;

        return {
            totalInvested,
            activeInvested,
            closedInvested,
            totalSold,
            currentHolding,
            realisedPnL,
            unrealisedPnL,
            netPnL,
            pnlPct,
            totalCount: ipoRows.length,
            activeCount,
            partialCount,
            closedCount
        };
    }, [portfolioData]);

    const activeColumnDefs = useMemo(() => {
        if (viewTab === 'ipo') {
            return [
                { field: "stock", headerName: "Scrip", flex: 1.2, minWidth: 120, pinned: 'left' },
                { 
                    field: "status", 
                    headerName: "Status", 
                    flex: 0.8, 
                    width: 90, 
                    cellRenderer: params => {
                        const status = params.data.status || (Number(params.data.quantity) > 0 ? "Active" : "Closed");
                        const badgeClass = status === 'Partially Closed' 
                            ? 'badge-status-partial' 
                            : (status === 'Active' ? 'badge-status-active' : 'badge-status-closed');
                        return (
                            <span className={badgeClass}>
                                {status === 'Partially Closed' ? 'Partial' : status}
                            </span>
                        );
                    }
                },
                { 
                    field: "allottedQty", 
                    headerName: "Allotted", 
                    flex: 0.8, 
                    width: 80, 
                    valueGetter: params => params.data.allottedQty || params.data.quantity || 0,
                    valueFormatter: p => formatINR(p.value) 
                },
                { 
                    field: "quantity", 
                    headerName: "Holding", 
                    flex: 0.8, 
                    width: 80, 
                    valueFormatter: p => formatINR(p.value) 
                },
                { 
                    field: "price", 
                    headerName: "Issue Price", 
                    flex: 0.9, 
                    width: 85, 
                    valueFormatter: p => "₹" + formatINR(p.value) 
                },
                { 
                    field: "totalInvestedAllTime", 
                    headerName: "Invested", 
                    flex: 1, 
                    minWidth: 100, 
                    valueGetter: params => params.data.totalInvestedAllTime || params.data.totalBuy || 0,
                    valueFormatter: p => "₹" + formatINR(p.value) 
                },
                { 
                    field: "totalSold", 
                    headerName: "Total Sold", 
                    flex: 1, 
                    minWidth: 100, 
                    valueFormatter: p => p.value ? "₹" + formatINR(p.value) : "—" 
                },
                { 
                    field: "totalValue", 
                    headerName: "Current Val", 
                    flex: 1, 
                    minWidth: 100, 
                    valueFormatter: p => Number(p.data.quantity) > 0 ? "₹" + formatINR(p.value) : "—" 
                },
                { 
                    field: "ltp", 
                    headerName: "LTP / Exit", 
                    flex: 0.9, 
                    width: 85, 
                    valueFormatter: p => p.value ? "₹" + formatINR(p.value) : "—" 
                },
                { 
                    field: "netPnL", 
                    headerName: "Net Profit", 
                    flex: 1, 
                    minWidth: 100,
                    valueGetter: params => params.data.netPnL !== undefined ? params.data.netPnL : (Number(params.data.quantity) > 0 ? params.data.unrealisedPnL : params.data.realisedPnL),
                    valueFormatter: p => "₹" + formatINR(p.value),
                    cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" },
                    cellStyle: { fontWeight: 'bold' }
                },
                { 
                    field: "pnlPercent", 
                    headerName: "ROI %", 
                    flex: 0.8, 
                    width: 85, 
                    cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" }, 
                    valueFormatter: p => (Number(p.value) || 0).toFixed(1) + "%" 
                }
            ];
        }

        if (viewTab === 'realised') {
            return [
                { field: "stock", headerName: "Scrip", flex: 1.2, pinned: 'left' },
                { 
                    headerName: "Capital Deployed", 
                    flex: 1,
                    // Get the total buy cost from the raw trades
                    valueGetter: params => {
                        const trades = rawRealisedData[params.data.stock] || [];
                        return trades.reduce((sum, t) => sum + (t.qty * t.buyPrice), 0);
                    },
                    valueFormatter: p => "₹" + formatINR(p.value),
                },
                { 
                    field: "realisedPnL", 
                    headerName: "Net Profit", 
                    flex: 1,
                    valueFormatter: p => "₹" + formatINR(p.value),
                    cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" },
                    cellStyle: { fontWeight: 'bold' }
                },
                { 
                    headerName: "ROI %", 
                    flex: 0.8,
                    valueGetter: params => {
                        const trades = rawRealisedData[params.data.stock] || [];
                        const buyCost = trades.reduce((sum, t) => sum + (t.qty * t.buyPrice), 0);
                        return buyCost !== 0 ? (params.data.realisedPnL / buyCost) * 100 : 0;
                    },
                    valueFormatter: p => p.value.toFixed(2) + "%",
                    cellClassRules: { 'text-green': "x > 0", 'text-red': "x < 0" }
                },
                { 
                    headerName: "Avg. Days", 
                    flex: 0.8,
                    valueGetter: params => {
                        const trades = rawRealisedData[params.data.stock] || [];
                        if (trades.length === 0) return 0;
                        const totalDays = trades.reduce((sum, t) => {
                            const days = Math.floor((new Date(t.sellDate) - new Date(t.buyDate)) / (1000 * 60 * 60 * 24));
                            return sum + days;
                        }, 0);
                        return Math.round(totalDays / trades.length);
                    },
                    valueFormatter: p => p.value + " d",
                    cellStyle: { color: '#94a3b8' }
                }
            ];
        }
        return columnDefs;
    }, [viewTab, columnDefs, formatINR, rawRealisedData]);

    const activePieData = chartType === 'sector' ? sectorData : stockAllocationData;

    if (loading) return (
        <div className="loading-container">
            <div className="financial-loader">
                <div className="bar"></div><div className="bar"></div><div className="bar"></div><div className="bar"></div><div className="bar"></div>
            </div>
            <h3 className="loading-text">Evaluating Positions</h3>
            <p className="loading-subtext">Fetching latest Market Data</p>
        </div>
    );

    const formatTooltipDate = (dateStr) => {
        if (!dateStr) return "";
        return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' });
    };

    const formatAxisDate = (dateStr) => {
        if (!dateStr) return "";
        return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
    };

    return (
        <div className="mf-dashboard stock-theme">
            
            <header className="mf-header">
                <div className="header-left-spacer"></div>
                <h1>Equity Portfolio</h1>
                <div className="header-controls">
                    <label className={`live-badge ${refresh ? "active" : ""}`}>
                        <input type="checkbox" checked={refresh} onChange={() => setRefresh(!refresh)} />
                        {refresh ? "● Live" : "○ Static"}
                    </label>
                    <div className="date-filters">
                        <input type="date" value={tempDate} onChange={e => setTempDate(e.target.value)} />
                        <button className="btn-update" onClick={() => setSelectedDate(tempDate)}>Go</button>
                    </div>
                </div>
            </header>
            <nav className="chrome-tabs-container">
                <div 
                    className={`chrome-tab ${viewTab === 'holdings' ? 'active' : ''}`} 
                    onClick={() => setViewTab('holdings')}
                >
                    💼 Active Holdings
                </div>
                <div 
                    className={`chrome-tab ${viewTab === 'realised' ? 'active' : ''}`} 
                    onClick={() => setViewTab('realised')}
                >
                    💰 Realised P&L
                </div>
                <div 
                    className={`chrome-tab ${viewTab === 'ipo' ? 'active' : ''}`} 
                    onClick={() => setViewTab('ipo')}
                >
                    🚀 IPO Corner
                </div>
            </nav>
            

            <section className="stats-grid">
                {viewTab === 'ipo' ? (
                    // DEDICATED 4 TILES FOR IPO CORNER (ACTIVE + CLOSED)
                    <>
                        <div className="stat-card">
                            <div className="card-icon" style={{background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6'}}>💰</div>
                            <div className="info">
                                <h3>Total Invested</h3>
                                <p>₹{formatINR(ipoSummary.totalInvested)}</p>
                                <span className="card-sub-info">
                                    Active: ₹{formatINR(ipoSummary.activeInvested)} | Closed: ₹{formatINR(ipoSummary.closedInvested)}
                                </span>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="card-icon" style={{background: 'rgba(168, 85, 247, 0.1)', color: '#a855f7'}}>💸</div>
                            <div className="info">
                                <h3>Total Sold</h3>
                                <p>₹{formatINR(ipoSummary.totalSold)}</p>
                                <span className="card-sub-info">
                                    Holding Val: ₹{formatINR(ipoSummary.currentHolding)}
                                </span>
                            </div>
                        </div>
                        <div className={`stat-card ${ipoSummary.netPnL >= 0 ? 'positive' : 'negative'}`}>
                            <div className="card-icon" style={{background: ipoSummary.netPnL >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: ipoSummary.netPnL >= 0 ? '#10b981' : '#ef4444'}}>
                                {ipoSummary.netPnL >= 0 ? '🚀' : '🔻'}
                            </div>
                            <div className="info">
                                <h3>Total Profit</h3>
                                <div className="value-row">
                                    <p>₹{formatINR(Math.abs(ipoSummary.netPnL))}</p>
                                    <span className="badge">{ipoSummary.pnlPct.toFixed(2)}%</span>
                                </div>
                                <span className="card-sub-info">
                                    Realised: ₹{formatINR(ipoSummary.realisedPnL)} | Unrealised: ₹{formatINR(ipoSummary.unrealisedPnL)}
                                </span>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="card-icon" style={{background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b'}}>📊</div>
                            <div className="info">
                                <h3>IPO Scrips</h3>
                                <p>{ipoSummary.totalCount} Scrips</p>
                                <span className="card-sub-info">
                                    {ipoSummary.activeCount} Open | {ipoSummary.partialCount} Partial | {ipoSummary.closedCount} Closed
                                </span>
                            </div>
                        </div>
                    </>
                ) : viewTab === 'holdings' ? (
                    // STANDARD 4 TILES FOR ACTIVE HOLDINGS
                    <>
                        <div className="stat-card">
                            <div className="card-icon" style={{background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6'}}>💰</div>
                            <div className="info"><h3>Invested Amount</h3><p>₹{formatINR(activeTabSummary.invested)}</p></div>
                        </div>
                        <div className="stat-card">
                            <div className="card-icon" style={{background: 'rgba(16, 185, 129, 0.1)', color: '#10b981'}}>📈</div>
                            <div className="info"><h3>Current Value</h3><p>₹{formatINR(activeTabSummary.current)}</p></div>
                        </div>
                        <div className={`stat-card ${activeTabSummary.pnl >= 0 ? 'positive' : 'negative'}`}>
                            <div className="card-icon" style={{background: activeTabSummary.pnl >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: activeTabSummary.pnl >= 0 ? '#10b981' : '#ef4444'}}>
                                {activeTabSummary.pnl >= 0 ? '🚀' : '🔻'}
                            </div>
                            <div className="info">
                                <h3>Total Returns</h3>
                                <div className="value-row">
                                    <p>₹{formatINR(Math.abs(activeTabSummary.pnl))}</p>
                                    <span className="badge">{activeTabSummary.pnlPct.toFixed(2)}%</span>
                                </div>
                            </div>
                        </div>
                        <div className={`stat-card ${activeTabSummary.today >= 0 ? 'positive' : 'negative'}`}>
                            <div className="card-icon" style={{background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b'}}>📅</div>
                            <div className="info">
                                <h3>Day's P&L</h3>
                                <div className="value-row">
                                    <p>₹{formatINR(Math.abs(activeTabSummary.today))}</p>
                                    <span className="badge">{activeTabSummary.todayPct.toFixed(2)}%</span>
                                </div>
                            </div>
                        </div>
                    </>
                ) : (
                    // FOCUS 3 TILES FOR REALISED P&L
                    <>
                        <div className="stat-card positive">
                            <div className="card-icon" style={{background: 'rgba(16, 185, 129, 0.1)', color: '#10b981'}}>💹</div>
                            <div className="info">
                                <h3>Total Gains</h3>
                                <p>₹{formatINR(summary.realisedGains)}</p>
                            </div>
                        </div>

                        <div className="stat-card negative">
                            <div className="card-icon" style={{background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444'}}>📉</div>
                            <div className="info">
                                <h3>Total Losses</h3>
                                <p>₹{formatINR(Math.abs(summary.realisedLosses))}</p>
                            </div>
                        </div>

                        <div className={`stat-card ${summary.totalRealised >= 0 ? 'positive' : 'net-blue'}`}>
                            <div className="card-icon" style={{
                                background: summary.totalRealised >= 0 ? 'rgba(59, 130, 246, 0.1)' : 'rgba(30, 41, 59, 0.1)', 
                                color: summary.totalRealised >= 0 ? '#3b82f6' : '#94a3b8'
                            }}>
                                🏦
                            </div>
                            <div className="info">
                                <h3>Net Realised P&L</h3>
                                <p>₹{formatINR(summary.totalRealised)}</p>
                            </div>
                        </div>

                        <div 
                            className="stat-card positive" 
                            style={{ cursor: 'pointer', transition: 'all 0.2s ease' }}
                            onDoubleClick={() => {
                                if (fetchTotalDividends) fetchTotalDividends();
                                setAllDividendsModalOpen(true);
                            }}
                            onClick={() => {
                                if (fetchTotalDividends) fetchTotalDividends();
                                setAllDividendsModalOpen(true);
                            }}
                        >
                            <div className="card-icon" style={{background: 'rgba(34, 197, 94, 0.1)', color: '#22c55e'}}>🎁</div>
                            <div className="info">
                                <h3>Total Dividends</h3>
                                <p>₹{formatINR(summary.totalDividends)}</p>
                                <span className="card-sub-info" style={{ color: '#10b981', fontSize: '11px', fontWeight: 600 }}>
                                    ✨ Click to view all
                                </span>
                            </div>
                        </div>
                    </>
                )}
            </section>

            <div className="content-stack">
                <div className="grid-container full-width">
                    <div className="grid-header-row">
                        <div className="grid-header-title">
                            <h3>
                                {viewTab === 'holdings' && "Active Portfolio"}
                                {viewTab === 'realised' && "Realised Profit & Loss Summary"}
                                {viewTab === 'ipo' && "Initial Public Offerings (IPO)"}
                            </h3>
                            <span className="holdings-count-badge">{filteredRowData.length} Items</span>
                        </div>

                        <div className="grid-header-controls">
                            {/* Quick Search */}
                            <div className="table-search-box">
                                <span className="search-icon">🔍</span>
                                <input 
                                    type="text" 
                                    placeholder="Search scrip..." 
                                    value={quickFilterText} 
                                    onChange={e => setQuickFilterText(e.target.value)} 
                                />
                            </div>

                            {/* Column Chooser Button & Popover (for Holdings View) */}
                            {viewTab === 'holdings' && ALL_EQUITY_COLUMNS.length > 0 && (
                                <div className="col-picker-container" ref={colPickerRef}>
                                    <button 
                                        className={`col-picker-btn ${showColPicker ? 'active' : ''}`}
                                        onClick={() => setShowColPicker(!showColPicker)}
                                        title="Customize Visible Columns"
                                    >
                                        <span>⚙️</span>
                                        <span>Columns</span>
                                        <span className="col-count-chip">
                                            {Object.values(visibleCols).filter(Boolean).length}/{ALL_EQUITY_COLUMNS.length}
                                        </span>
                                    </button>

                                    {showColPicker && (
                                        <div className="col-picker-dropdown">
                                            <div className="col-picker-header">
                                                <h4>Visible Columns</h4>
                                                <div className="col-picker-actions">
                                                    <button onClick={selectAllColumns}>All</button>
                                                    <button onClick={deselectAllColumns}>None</button>
                                                    <button onClick={resetDefaultColumns}>Reset</button>
                                                </div>
                                            </div>

                                            <div className="col-search-input">
                                                <input 
                                                    type="text" 
                                                    placeholder="Filter column list..." 
                                                    value={colSearchQuery} 
                                                    onChange={e => setColSearchQuery(e.target.value)} 
                                                    autoFocus
                                                />
                                            </div>

                                            <div className="col-picker-list">
                                                {ALL_EQUITY_COLUMNS
                                                    .filter(col => col.headerName.toLowerCase().includes(colSearchQuery.toLowerCase()))
                                                    .map(col => (
                                                        <label key={col.id} className="col-checkbox-label">
                                                            <input 
                                                                type="checkbox" 
                                                                checked={!!visibleCols[col.id]} 
                                                                onChange={() => toggleColumn(col.id)} 
                                                                disabled={col.id === 'stock'} 
                                                            />
                                                            <span className="col-name-text">{col.headerName}</span>
                                                            {col.defaultVisible && <span className="default-pill">Default</span>}
                                                        </label>
                                                    ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="ag-theme-alpine table-wrapper">
                        <AgGridReact
                            ref={gridRef}
                            rowData={filteredRowData}
                            columnDefs={activeColumnDefs}
                            defaultColDef={{ sortable: true, filter: true, resizable: true }}
                            pagination={true}
                            paginationPageSize={30}
                            paginationPageSizeSelector={[10, 20, 30, 50, 100]}
                            quickFilterText={quickFilterText}
                            onRowDoubleClicked={onRowDoubleClicked}
                        />
                    </div>
                </div>

                <div className="charts-row">
                    {/* --- 1. TREND CHART --- */}
                    <div className="chart-container trend-box">
                        <div className="chart-card-header">
                            <div className="chart-card-title-group">
                                <h3 className="chart-card-title">Growth Trend</h3>
                                {trendStats && (
                                    <span className={`trend-badge ${trendStats.isPositive ? 'pos' : 'neg'}`}>
                                        {trendStats.isPositive ? '▲ +' : '▼ '}₹{formatINR(Math.abs(trendStats.diff))} ({trendStats.isPositive ? '+' : ''}{trendStats.percent.toFixed(2)}%)
                                    </span>
                                )}
                            </div>
                            
                            <div className="trend-timeframe-group">
                                {['1M', '3M', '6M', '1Y', 'ALL'].map(tf => (
                                    <button 
                                        key={tf} 
                                        className={`timeframe-btn ${trendTimeframe === tf ? 'active' : ''}`} 
                                        onClick={() => setTrendTimeframe(tf)}
                                    >
                                        {tf}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {trendStats && (
                            <div className="trend-legend-pills">
                                <span className="trend-pill">
                                    <span className="dot dot-value"></span>
                                    <span className="pill-label">Current:</span>
                                    <strong className="pill-val">₹{formatINR(trendStats.currentVal)}</strong>
                                </span>
                                <span className="trend-pill">
                                    <span className="dot dot-invested"></span>
                                    <span className="pill-label">Invested:</span>
                                    <strong className="pill-val">₹{formatINR(trendStats.investedVal)}</strong>
                                </span>
                            </div>
                        )}

                        <div style={{ flex: 1, width: '100%', minHeight: 0 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={filteredTrendData} margin={{ top: 10, right: 15, left: -5, bottom: 5 }}>
                                    <defs>
                                        <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.25}/>
                                            <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0}/>
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                    <XAxis 
                                        dataKey="date" 
                                        tickFormatter={formatAxisDate} 
                                        stroke="#94a3b8" 
                                        fontSize={12} 
                                        tickLine={false} 
                                        axisLine={false} 
                                        minTickGap={35} 
                                    />
                                    <YAxis 
                                        domain={['auto', 'auto']}
                                        stroke="#94a3b8" 
                                        fontSize={12} 
                                        tickLine={false} 
                                        axisLine={false} 
                                        tickFormatter={formatCompactINR}
                                        width={65}
                                    />
                                    <Tooltip content={<CustomTrendTooltip />} />
                                    <Area 
                                        type="monotone" 
                                        dataKey="value" 
                                        stroke="#38bdf8" 
                                        fill="url(#colorVal)" 
                                        strokeWidth={2} 
                                        name="Current Value"
                                        activeDot={{ r: 5, stroke: '#38bdf8', strokeWidth: 2, fill: '#fff' }} 
                                    />
                                    <Area 
                                        type="monotone" 
                                        dataKey="invested" 
                                        stroke="#c084fc" 
                                        fill="transparent" 
                                        strokeWidth={1.8} 
                                        name="Invested Amount" 
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* --- 2. PIE CHART (Fixed Legend Overflow) --- */}
                    <div className="chart-container donut-box">
                        <div className="chart-card-header">
                            <div className="chart-card-title-group">
                                <h3 className="chart-card-title">Allocation</h3>
                            </div>
                            <div className="chart-toggle">
                                <button className={chartType === 'sector' ? 'active' : ''} onClick={() => setChartType('sector')}>Sector</button>
                                <button className={chartType === 'stock' ? 'active' : ''} onClick={() => setChartType('stock')}>Stock</button>
                            </div>
                        </div>

                        <div className="allocation-legend-spacer">
                            <span className="allocation-subtitle">
                                {chartType === 'sector' ? '• Sector Exposure Breakdown' : '• Top 10 Scrip Concentration'}
                            </span>
                        </div>
                        
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                                <Pie 
                                    data={activePieData} 
                                    innerRadius={60} 
                                    outerRadius={90} 
                                    paddingAngle={3} 
                                    dataKey="value" 
                                    stroke="none"
                                >
                                    {activePieData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                                </Pie>
                                <Tooltip 
                                    formatter={(value) => `₹${formatINR(value)}`}
                                    contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', color: '#0f172a', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                    itemStyle={{ color: '#0f172a', fontWeight: 600 }}
                                />
                                {/* Clean Vertical Legend on the Right */}
                                <Legend 
                                    layout="vertical" 
                                    verticalAlign="middle" 
                                    align="right"
                                    iconType="circle"
                                    iconSize={8}
                                    wrapperStyle={{ fontSize: '12px', color: '#334155', fontWeight: 500 }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {modalOpen && (
                <div className="portfolio-modal-overlay" onClick={() => setModalOpen(false)}>
                    <div className="portfolio-modal-content" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <h2>{selectedRowData?.stock} Analysis</h2>
                                <div className="modal-tabs">
                                    <button 
                                        className={`tab-btn ${activeTab === 'transactions' ? 'active' : ''}`}
                                        // Trigger handleTabChange instead of just setActiveTab
                                        onClick={() => handleTabChange('transactions')}
                                    >
                                        Transactions
                                    </button>
                                    <button 
                                        className={`tab-btn ${activeTab === 'chart' ? 'active' : ''}`}
                                        // Trigger handleTabChange to initiate the fetch
                                        onClick={() => handleTabChange('chart')}
                                    >
                                        Performance
                                    </button>
                                    <button 
                                        className={`tab-btn ${activeTab === 'dividends' ? 'active' : ''}`}
                                        onClick={() => handleTabChange('dividends')}
                                    >
                                        Dividends
                                    </button>
                                </div>
                            </div>
                            <button className="close-btn" onClick={() => setModalOpen(false)}>×</button>
                        </div>

                        <div className="modal-body">
                            <div className={`dummy-stats-row ${viewTab === 'realised' ? 'four-cards' : 'six-cards'}`}>
                            {viewTab !== 'realised' ? (
                                <>
                                    <div className="d-card"><span>Invested</span><p>{formatCurrency(selectedRowData?.totalBuy)}</p></div>
                                    <div className="d-card"><span>Current</span><p>{formatCurrency(selectedRowData?.totalValue)}</p></div>
                                    <div className={`d-card ${selectedRowData?.unrealisedPnL >= 0 ? 'pos' : 'neg'}`}><span>Total P&L</span><p>{formatCurrency(selectedRowData?.unrealisedPnL)}</p></div>
                                    
                                    {/* Realized Block */}
                                    <div className={`d-card ${stockRealized >= 0 ? 'pos' : 'neg'}`}>
                                        <span>Realized</span>
                                        <p>{formatCurrency(stockRealized)}</p>
                                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', fontSize: '11px', marginTop: '6px', opacity: 0.85 }}>
                                            <span title="< 365 Days">STCG: {formatCurrency(realizedSTCG)}</span>
                                            <span style={{ opacity: 0.4 }}>|</span>
                                            <span title=">= 365 Days">LTCG: {formatCurrency(realizedLTCG)}</span>
                                        </div>
                                    </div>

                                    {/* Unrealized Block */}
                                    <div className={`d-card ${stockUnrealized >= 0 ? 'pos' : 'neg'}`}>
                                        <span>Unrealized</span>
                                        <p>{formatCurrency(stockUnrealized)}</p>
                                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', fontSize: '11px', marginTop: '6px', opacity: 0.85 }}>
                                            <span title="< 365 Days">STCG: {formatCurrency(unrealizedSTCG)}</span>
                                            <span style={{ opacity: 0.4 }}>|</span>
                                            <span title=">= 365 Days">LTCG: {formatCurrency(unrealizedLTCG)}</span>
                                        </div>
                                    </div>

                                    <div className={`d-card ${totalScripDividends > 0 ? 'pos' : ''}`}>
                                        <span>Total Dividends</span>
                                        <p>{formatCurrency(totalScripDividends)}</p>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="d-card pos">
                                        <span>Total Gain</span>
                                        <p>{formatCurrency((selectedRowData?.transactionSummary || [])
                                            .filter(t => t.pnl > 0)
                                            .reduce((sum, t) => sum + t.pnl, 0))}</p>
                                    </div>
                                    <div className="d-card neg">
                                        <span>Total Loss</span>
                                        <p>{formatCurrency(Math.abs((selectedRowData?.transactionSummary || [])
                                            .filter(t => t.pnl < 0)
                                            .reduce((sum, t) => sum + t.pnl, 0)))}</p>
                                    </div>
                                    
                                    {/* Net Realised Block */}
                                    <div className={`d-card ${selectedRowData?.realisedPnL >= 0 ? 'pos' : 'neg'}`}>
                                        <span>Net Realised</span>
                                        <p>{formatCurrency(selectedRowData?.realisedPnL)}</p>
                                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', fontSize: '11px', marginTop: '6px', opacity: 0.85 }}>
                                            <span title="< 365 Days">STCG: {formatCurrency(realizedSTCG)}</span>
                                            <span style={{ opacity: 0.4 }}>|</span>
                                            <span title=">= 365 Days">LTCG: {formatCurrency(realizedLTCG)}</span>
                                        </div>
                                    </div>

                                    <div className={`d-card ${totalScripDividends > 0 ? 'pos' : ''}`}>
                                        <span>Total Dividends</span>
                                        <p>{formatCurrency(totalScripDividends)}</p>
                                    </div>
                                </>
                            )}
                        </div>

                            {/* Tab Content Section */}
                            <div className="tab-content-wrapper">
                                {activeTab === 'transactions' ? (
                                    <div className="dummy-grid-container ag-theme-balham-dark" style={{ height: '100%', width: '100%', flex: 1 }}>
                                        <AgGridReact
                                            rowData={
                                                viewTab === 'realised' 
                                                    ? (selectedRowData?.transactionSummary || []).filter(trx => trx.status === 'Closed')
                                                    : (selectedRowData?.transactionSummary || [])
                                            }
                                            columnDefs={transactionColumnDefs} 
                                            defaultColDef={{ resizable: true, sortable: true, filter: true, minWidth: 100, maxWidth: 170}}
                                            pagination={false}
                                        />
                                    </div>
                                ) : activeTab === 'dividends' ? (
                                    <div className="dummy-grid-container ag-theme-balham-dark" style={{ height: '100%', width: '100%', flex: 1 }}>
                                        <AgGridReact
                                            rowData={dividendData || []}
                                            columnDefs={[
                                                { 
                                                    field: 'payoutDate', 
                                                    headerName: 'Date', 
                                                    flex: 1, 
                                                    minWidth: 120, 
                                                    filter: 'agDateColumnFilter', 
                                                    sort: 'asc',
                                                    comparator: (d1, d2) => {
                                                        if (!d1 && !d2) return 0;
                                                        if (!d1) return -1;
                                                        if (!d2) return 1;
                                                        return new Date(d1).getTime() - new Date(d2).getTime();
                                                    },
                                                    cellStyle: params => params.node.isRowPinned() ? { fontWeight: 'bold' } : null
                                                },
                                                { 
                                                    field: 'dividendAmount', 
                                                    headerName: 'Dividend Amount (₹)', 
                                                    flex: 1, 
                                                    minWidth: 140, 
                                                    filter: 'agNumberColumnFilter', 
                                                    valueFormatter: (params) => (params.value != null && params.value !== '') ? `₹${formatINR(params.value)}` : '' 
                                                },
                                                { 
                                                    field: 'quantity', 
                                                    headerName: 'Quantity Held', 
                                                    flex: 1, 
                                                    minWidth: 120, 
                                                    filter: 'agNumberColumnFilter',
                                                    valueFormatter: (params) => (params.value != null && params.value !== '') ? params.value : ''
                                                },
                                                { 
                                                    field: 'totalDividend', 
                                                    headerName: 'Total Dividend (₹)', 
                                                    flex: 1.2, 
                                                    minWidth: 140, 
                                                    filter: 'agNumberColumnFilter', 
                                                    valueFormatter: (params) => (params.value != null && params.value !== '') ? `₹${formatINR(params.value)}` : '',
                                                    cellStyle: params => params.node.isRowPinned() ? { fontWeight: 'bold', color: '#10b981' } : null
                                                }
                                            ]}
                                            pinnedBottomRowData={
                                                dividendData && dividendData.length > 0 ? [{
                                                    payoutDate: 'Total',
                                                    dividendAmount: null,
                                                    quantity: null,
                                                    totalDividend: totalScripDividends
                                                }] : []
                                            }
                                            defaultColDef={{ resizable: true, sortable: true, filter: true, flex: 1, minWidth: 100 }}
                                            autoSizeStrategy={{ type: 'fitGridWidth' }}
                                            onGridReady={(params) => params.api.sizeColumnsToFit()}
                                            pagination={false}
                                        />
                                    </div>
                                ) : (
                                    <div className="modal-chart-box" style={{ height: '100%', width: '100%', flex: 1, userSelect: 'none' }}>
                                        <div className="chart-header-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                                                <h3>Price Performance & Analytics</h3>
                                                {zoomState.data.length !== scripHistory.length && (
                                                    <button className="toggle-chip active" onClick={resetZoom} style={{ cursor: 'pointer' }}>
                                                        ↺ Reset Zoom
                                                    </button>
                                                )}
                                            </div>
                                            <div className="chart-controls">
                                                {Object.keys(visibleLines).map(key => (
                                                    <label key={key} className={`toggle-chip ${visibleLines[key] ? 'active' : ''}`}>
                                                        <input 
                                                            type="checkbox" 
                                                            checked={visibleLines[key]} 
                                                            onChange={() => toggleLine(key)} 
                                                            style={{ display: 'none' }} 
                                                        />
                                                        {key.toUpperCase()}
                                                    </label>
                                                ))}
                                            </div>
                                        </div>
                                        
                                        {isHistoryLoading ? (
                                            <div className="mini-loader">Fetching historical data...</div>
                                        ) : (
                                            <ResponsiveContainer width="100%" height="90%">
                                                <AreaChart 
                                                    data={zoomState.data}
                                                    onMouseDown={(e) => e && setZoomState({ ...zoomState, refAreaLeft: e.activeLabel })}
                                                    onMouseMove={(e) => zoomState.refAreaLeft && setZoomState({ ...zoomState, refAreaRight: e.activeLabel })}
                                                    onMouseUp={handleZoom}
                                                >
                                                    <defs>
                                                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                                                        </linearGradient>
                                                    </defs>
                                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                                                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={10} tickFormatter={formatAxisDate} />
                                                    <YAxis stroke="#94a3b8" fontSize={10} domain={['auto', 'auto']} tickFormatter={val => `₹${formatINR(val)}`} />
                                                    <Tooltip 
                                                        cursor={{ 
                                                            stroke: '#94a3b8', 
                                                            strokeWidth: 1, 
                                                            strokeDasharray: '5 5',
                                                            strokeOpacity: 0.4 // Fixed your 14 value to a visible 0.4
                                                        }}
                                                        contentStyle={{ 
                                                            background: '#1e293b', 
                                                            border: '1px solid #334155', 
                                                            borderRadius: '8px' 
                                                        }}
                                                        labelStyle={{ color: '#3b82f6', fontWeight: 'bold' }}
                                                        itemStyle={{ color: '#fff', fontSize: '12px' }} 
                                                        labelFormatter={formatTooltipDate}
                                                        formatter={(val, name) => [`₹${formatINR(val)}`, name]}
                                                    />
                                                    <Legend verticalAlign="top" height={36} />
                                                    
                                                    <Area 
                                                        type="monotone" 
                                                        dataKey="price" 
                                                        stroke="#3b82f6" 
                                                        fill="url(#colorPrice)" 
                                                        strokeWidth={2} 
                                                        name="Price" 
                                                        connectNulls
                                                    />
                                                    
                                                    {visibleLines.ema20 && (
                                                        <Area type="monotone" dataKey="ema20" stroke="#f59e0b" fill="transparent" strokeWidth={2} name="20 EMA" connectNulls />
                                                    )}
                                                    {visibleLines.ema50 && (
                                                        <Area type="monotone" dataKey="ema50" stroke="#8b5cf6" fill="transparent" strokeWidth={2} name="50 EMA" connectNulls />
                                                    )}
                                                    {visibleLines.ema100 && (
                                                        <Area type="monotone" dataKey="ema100" stroke="#ec4899" fill="transparent" strokeWidth={2} name="100 EMA" connectNulls />
                                                    )}
                                                    {visibleLines.ema200 && (
                                                        <Area type="monotone" dataKey="ema200" stroke="#10b981" fill="transparent" strokeWidth={2} name="200 EMA" connectNulls />
                                                    )}

                                                    {/* ZOOM SELECTION OVERLAY */}
                                                    {zoomState.refAreaLeft && zoomState.refAreaRight ? (
                                                        <ReferenceArea 
                                                            x1={zoomState.refAreaLeft} 
                                                            x2={zoomState.refAreaRight} 
                                                            strokeOpacity={0.3} 
                                                            fill="#3b82f6" 
                                                            fillOpacity={0.1} 
                                                        />
                                                    ) : null}
                                                </AreaChart>
                                            </ResponsiveContainer>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* --- ALL DIVIDENDS DIALOG --- */}
            {allDividendsModalOpen && (
                <div className="portfolio-modal-overlay" onClick={() => setAllDividendsModalOpen(false)}>
                    <div className="portfolio-modal-content" style={{ maxWidth: '1750px', width: '95vw', height: '92vh' }} onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <h2>🎁 Dividend Income Summary</h2>
                                <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: '13px' }}>
                                    All dividend payouts received across your entire portfolio
                                </p>
                            </div>
                            <button className="close-btn" onClick={() => setAllDividendsModalOpen(false)}>×</button>
                        </div>

                        <div className="modal-body">
                            <div className="dummy-stats-row four-cards">
                                <div className="d-card pos">
                                    <span>Total Dividends</span>
                                    <p>₹{formatINR(summary.totalDividends)}</p>
                                </div>
                                <div className="d-card">
                                    <span>Total Payouts</span>
                                    <p>{summary.dividendsList?.length || 0}</p>
                                </div>
                                <div className="d-card">
                                    <span>Companies</span>
                                    <p>{new Set((summary.dividendsList || []).map(d => d.stock)).size}</p>
                                </div>
                                <div className="d-card">
                                    <span>Avg Payout</span>
                                    <p>₹{summary.dividendsList && summary.dividendsList.length > 0 ? formatINR(summary.totalDividends / summary.dividendsList.length) : "0"}</p>
                                </div>
                            </div>

                            <div className="tab-content-wrapper" style={{ marginTop: '14px', flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                                <div className="dummy-grid-container ag-theme-balham-dark" style={{ height: '100%', width: '100%', flex: 1 }}>
                                    <AgGridReact
                                        rowData={summary.dividendsList || []}
                                        columnDefs={allDividendsColumnDefs}
                                        defaultColDef={{ resizable: true, sortable: true, filter: true }}
                                        pagination={true}
                                        paginationPageSize={50}
                                        paginationPageSizeSelector={[20, 50, 100]}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PortfolioUI;