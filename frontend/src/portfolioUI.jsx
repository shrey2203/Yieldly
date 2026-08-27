import React, { useState, useMemo, useEffect } from "react";
import { AgGridReact } from "ag-grid-react";
import { 
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend, Line, ReferenceArea
} from "recharts";

// Expanded color palette to handle more sectors if needed
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#6366f1', '#a855f7', '#14b8a6'];

const PortfolioUI = ({
    gridRef, portfolioData, chartData, sectorData, summary, columnDefs, 
    loading, refresh, setRefresh, tempDate, setTempDate, setSelectedDate, formatINR, viewTab, setViewTab, onRowDoubleClicked, modalOpen, setModalOpen, selectedRowData, transactionColumnDefs, activeTab, setActiveTab,
    scripHistory, isHistoryLoading, fetchScripPerformance, fetchScripDividends, dividendData, rawRealisedData
}) => {
    const [chartType, setChartType] = useState('sector'); 
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
            return portfolioData.filter(item => item.isIPO || item.type === 'IPO');
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
        
        return portfolioData;
    }, [viewTab, portfolioData, summary]);

    const activeColumnDefs = useMemo(() => {
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
                {viewTab != 'realised' ? (
                    // STANDARD 4 TILES FOR HOLDINGS / IPO
                    <>
                        <div className="stat-card">
                            <div className="card-icon" style={{background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6'}}>💰</div>
                            <div className="info"><h3>Invested Amount</h3><p>₹{formatINR(summary.invested)}</p></div>
                        </div>
                        <div className="stat-card">
                            <div className="card-icon" style={{background: 'rgba(16, 185, 129, 0.1)', color: '#10b981'}}>📈</div>
                            <div className="info"><h3>Current Value</h3><p>₹{formatINR(summary.current)}</p></div>
                        </div>
                        <div className={`stat-card ${summary.pnl >= 0 ? 'positive' : 'negative'}`}>
                            <div className="card-icon" style={{background: summary.pnl >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: summary.pnl >= 0 ? '#10b981' : '#ef4444'}}>
                                {summary.pnl >= 0 ? '🚀' : '🔻'}
                            </div>
                            <div className="info">
                                <h3>Total Returns</h3>
                                <div className="value-row">
                                    <p>₹{formatINR(Math.abs(summary.pnl))}</p>
                                    <span className="badge">{summary.pnlPct.toFixed(2)}%</span>
                                </div>
                            </div>
                        </div>
                        <div className={`stat-card ${summary.today >= 0 ? 'positive' : 'negative'}`}>
                            <div className="card-icon" style={{background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b'}}>📅</div>
                            <div className="info">
                                <h3>Day's P&L</h3>
                                <div className="value-row">
                                    <p>₹{formatINR(Math.abs(summary.today))}</p>
                                    <span className="badge">{summary.todayPct.toFixed(2)}%</span>
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

                        <div className="stat-card positive">
                            <div className="card-icon" style={{background: 'rgba(34, 197, 94, 0.1)', color: '#22c55e'}}>🎁</div>
                            <div className="info">
                                <h3>Total Dividends</h3>
                                <p>₹{formatINR(summary.totalDividends)}</p>
                            </div>
                        </div>
                    </>
                )}
            </section>

            <div className="content-stack">
                <div className="grid-container full-width">
                    <h3>
                        {viewTab === 'holdings' && "Active Portfolio"}
                        {viewTab === 'realised' && "Realised Profit & Loss Summary"}
                        {viewTab === 'ipo' && "Initial Public Offerings (IPO)"}
                    </h3>
                    <div className="ag-theme-balham-dark table-wrapper">
                        <AgGridReact
                            ref={gridRef}
                            rowData={filteredRowData}
                            columnDefs={activeColumnDefs}
                            defaultColDef={{ sortable: true, filter: true, resizable: true }}
                            pagination={true}
                            paginationPageSize={30}
                            onRowDoubleClicked={onRowDoubleClicked}
                        />
                    </div>
                </div>

                <div className="charts-row">
                    {/* --- 1. TREND CHART (Fixed Legend) --- */}
                    <div className="chart-container trend-box">
                        <div className="container-header"><h3>Growth Trend</h3></div>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
                                <defs>
                                    <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                                <XAxis dataKey="date" tickFormatter={formatAxisDate} stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} minTickGap={30} />
                                <YAxis hide />
                                <Tooltip 
                                    contentStyle={{background:'#1e293b', border:'1px solid #334155', borderRadius:'8px', color: '#fff'}}
                                    itemStyle={{ color: '#fff' }}
                                    labelFormatter={formatTooltipDate}
                                    formatter={(value, name) => [`₹${formatINR(value)}`, name === "value" ? "Current Value" : "Invested Amount"]}
                                />
                                {/* Legend Moved to Top Right to avoid overlap */}
                                <Legend verticalAlign="top" align="right" height={36} iconType="plainline" wrapperStyle={{top: -5, right: 0}}/>
                                <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="url(#colorVal)" strokeWidth={3} name="value" />
                                <Area type="monotone" dataKey="invested" stroke="#8b5cf6" fill="transparent" strokeDasharray="5 5" strokeWidth={2} name="invested" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>

                    {/* --- 2. PIE CHART (Fixed Legend Overflow) --- */}
                    <div className="chart-container donut-box">
                        <div className="container-header">
                            <h3>Allocation</h3>
                            <div className="chart-toggle">
                                <button className={chartType === 'sector' ? 'active' : ''} onClick={() => setChartType('sector')}>Sector</button>
                                <button className={chartType === 'stock' ? 'active' : ''} onClick={() => setChartType('stock')}>Stock</button>
                            </div>
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
                                    contentStyle={{background:'#1e293b', border:'1px solid #334155', borderRadius:'8px', color: '#fff'}}
                                    itemStyle={{ color: '#fff' }}
                                />
                                {/* Clean Vertical Legend on the Right */}
                                <Legend 
                                    layout="vertical" 
                                    verticalAlign="middle" 
                                    align="right"
                                    iconType="circle"
                                    iconSize={8}
                                    wrapperStyle={{ fontSize: '11px', color: '#cbd5e1' }}
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
                            <div className={`dummy-stats-row ${viewTab === 'realised' ? 'three-cards' : 'five-cards'}`}>
                            {viewTab !== 'realised' ? (
                                <>
                                    <div className="d-card"><span>Invested</span><p>₹{formatINR(selectedRowData?.totalBuy)}</p></div>
                                    <div className="d-card"><span>Current</span><p>₹{formatINR(selectedRowData?.totalValue)}</p></div>
                                    <div className={`d-card ${selectedRowData?.unrealisedPnL >= 0 ? 'pos' : 'neg'}`}><span>Total P&L</span><p>₹{formatINR(selectedRowData?.unrealisedPnL)}</p></div>
                                    
                                    {/* Realized Block Updated */}
                                    <div className={`d-card ${stockRealized >= 0 ? 'pos' : 'neg'}`}>
                                        <span>Realized</span>
                                        <p>₹{formatINR(stockRealized)}</p>
                                        {/* Replaced space-between with a 15px gap */}
                                        <div style={{ display: 'flex', gap: '15px', paddingLeft: '70px', fontSize: '11px', marginTop: '6px', opacity: 0.85 }}>
                                            <span title="< 365 Days">STCG: ₹{formatINR(realizedSTCG)}</span>
                                            <span title=">= 365 Days">LTCG: ₹{formatINR(realizedLTCG)}</span>
                                        </div>
                                    </div>

                                    <div className={`d-card ${stockUnrealized >= 0 ? 'pos' : 'neg'}`}>
                                        <span>Unrealized</span>
                                        <p>₹{formatINR(stockUnrealized)}</p>
                                        {/* Replaced space-between with a 15px gap */}
                                        <div style={{ display: 'flex', gap: '15px', paddingLeft: '70px', fontSize: '11px', marginTop: '6px', opacity: 0.85 }}>
                                            <span title="< 365 Days">STCG: ₹{formatINR(unrealizedSTCG)}</span>
                                            <span title=">= 365 Days">LTCG: ₹{formatINR(unrealizedLTCG)}</span>
                                        </div>
                            </div>
                                </>
                            ) : (
                                <>
                                    <div className="d-card pos">
                                        <span>Total Gain</span>
                                        <p>₹{formatINR((selectedRowData?.transactionSummary || [])
                                            .filter(t => t.pnl > 0)
                                            .reduce((sum, t) => sum + t.pnl, 0))}</p>
                                    </div>
                                    <div className="d-card neg">
                                        <span>Total Loss</span>
                                        <p>₹{formatINR(Math.abs((selectedRowData?.transactionSummary || [])
                                            .filter(t => t.pnl < 0)
                                            .reduce((sum, t) => sum + t.pnl, 0)))}</p>
                                    </div>
                                    
                                    {/* Net Realised Block in 'realised' tab also updated for consistency */}
                                    <div className={`d-card ${selectedRowData?.realisedPnL >= 0 ? 'pos' : 'neg'}`}>
                                        <span>Net Realised</span>
                                        <p>₹{formatINR(selectedRowData?.realisedPnL)}</p>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginTop: '6px', opacity: 0.85 }}>
                                            <span title="< 365 Days">STCG: ₹{formatINR(realizedSTCG)}</span>
                                            <span title=">= 365 Days">LTCG: ₹{formatINR(realizedLTCG)}</span>
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>

                            {/* Tab Content Section */}
                            <div className="tab-content-wrapper">
                                {activeTab === 'transactions' ? (
                                    <div className="dummy-grid-container ag-theme-balham-dark" style={{ height: '700px' }}>
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
                                    <div className="dummy-grid-container ag-theme-balham-dark" style={{ height: '700px' }}>
                                        <AgGridReact
                                            rowData={dividendData || []}
                                            columnDefs={[
                                                { field: 'payoutDate', headerName: 'Date', width: 120, filter: 'agDateColumnFilter', sort: 'desc' },
                                                { field: 'dividendAmount', headerName: 'Dividend Amount (₹)', width: 150, filter: 'agNumberColumnFilter', valueFormatter: (params) => `₹${formatINR(params.value)}` },
                                                { field: 'quantity', headerName: 'Quantity Held', width: 130, filter: 'agNumberColumnFilter' },
                                                { field: 'totalDividend', headerName: 'Total Dividend (₹)', width: 150, filter: 'agNumberColumnFilter', valueFormatter: (params) => `₹${formatINR(params.value)}` }
                                            ]}
                                            defaultColDef={{ resizable: true, sortable: true, filter: true, minWidth: 100, maxWidth: 200}}
                                            pagination={false}
                                        />
                                    </div>
                                ) : (
                                    <div className="modal-chart-box" style={{ height: '400px', userSelect: 'none' }}>
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
        </div>
    );
};

export default PortfolioUI;