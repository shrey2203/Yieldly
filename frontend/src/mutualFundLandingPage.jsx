import { 
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from "recharts";
import { AgGridReact } from "ag-grid-react";
import { useState, useEffect, useMemo, useRef } from "react";
import { AllCommunityModule, ModuleRegistry } from "ag-grid-community";
import "./mutualFund.css";

// Register AG Grid Modules
ModuleRegistry.registerModules([AllCommunityModule]);

const MutualFund = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    const userId = localStorage.getItem("username");
    
    // State for Summary Cards
    const [summary, setSummary] = useState({
        invested: 0,
        current: 0,
        unrealised: 0,
        unrealisedPct: 0,
        today: 0,
        todayPct: 0,
        ltcg: 0,
        stcg: 0
    });

    const [mutualFundData, setMutualFundData] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [filteredChartData, setFilteredChartData] = useState([]);

    // Filters & UI State
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedFund, setSelectedFund] = useState(null);

    // Close modal on Escape key press
    useEffect(() => {
        const handleKeyDown = (event) => {
            if (event.key === "Escape" || event.key === "Esc" || event.keyCode === 27) {
                setModalOpen(false);
                setShowColPicker(false);
            }
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, []);

    // --- HELPER: Indian Number Formatting ---
    const formatINR = (number) => {
        if (number === null || number === undefined) return "0";
        return Number(number).toLocaleString('en-IN', {
            maximumFractionDigits: 0, 
        });
    };

    const formatCurrency = (number) => {
        if (number === null || number === undefined) return "";
        return "₹ " + Number(number).toLocaleString('en-IN', {
            maximumFractionDigits: 0, 
        });
    };

    useEffect(() => {
        fetchMutualFundDetailed();
    }, []);

    useEffect(() => {
        if(chartData.length > 0) filterChartData();
    }, [chartData, startDate, endDate]);

    const fetchMutualFundDetailed = async () => {
        try {
            const response = await fetch(`api/fetchMutualFundData?userId=${userId}`, {
                 headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } 
            });
            const data = await response.json();

            // 1. Process Summary Data
            const pnl = data.totalCurrentSum - data.totalInvestedSum;
            setSummary({
                invested: data.totalInvestedSum,
                current: data.totalCurrentSum,
                unrealised: pnl,
                unrealisedPct: (pnl * 100) / data.totalCurrentSum,
                today: data.todayPNL,
                todayPct: (data.todayPNL * 100) / data.totalCurrentSum,
                ltcg: data.ltcg,
                stcg: data.stcg
            });

            // 2. Process Table Data
            if (data.mutualFunds) {
                setMutualFundData(data.mutualFunds.map(fund => ({
                    ...fund,
                    profitLoss: fund.totalCurrentValue - fund.totalInvestment
                })));
            }

            // 3. Process Chart Data
            if (data.mutualFundDayWiseCurrentAndTotalValue) {
                const formattedTrend = Object.entries(data.mutualFundDayWiseCurrentAndTotalValue)
                    .sort((a, b) => new Date(a[0]) - new Date(b[0]))
                    .map(([date, item]) => ({
                        date,
                        invested: Number(item.totalInvestment),
                        value: Number(item.currentInvestment)
                    }));
                setChartData(formattedTrend);
            }
            setLoading(false);
        } catch (err) {
            console.error(err);
            setError("Failed to load data.");
            setLoading(false);
        }
    };

    const filterChartData = () => {
        if (!startDate && !endDate) {
            setFilteredChartData(chartData);
            return;
        }
        const from = startDate ? new Date(startDate) : new Date("2000-01-01");
        const to = endDate ? new Date(endDate) : new Date();

        setFilteredChartData(chartData.filter(item => {
            const d = new Date(item.date);
            return d >= from && d <= to;
        }));
    };

    // --- MASTER AG GRID COLUMN DEFINITIONS ---
    const ALL_MF_COLUMNS = useMemo(() => [
        { id: "name", headerName: "Fund Name", field: "name", flex: 2, minWidth: 200, sortable: true, filter: true, defaultVisible: true },
        { id: "mutualFundNAV", headerName: "NAV", field: "mutualFundNAV", flex: 1, minWidth: 95, sortable: true, valueFormatter: p => (p.value ? Number(p.value).toFixed(2) : ""), defaultVisible: true },
        { id: "averageNav", headerName: "Avg NAV", field: "averageNav", flex: 1, minWidth: 95, sortable: true, valueFormatter: p => (p.value ? Number(p.value).toFixed(2) : ""), defaultVisible: false },
        { id: "totalUnits", headerName: "Total Units", field: "totalUnits", flex: 1, minWidth: 105, sortable: true, valueFormatter: p => (p.value ? Number(p.value).toFixed(3) : ""), defaultVisible: false },
        { id: "totalInvestment", headerName: "Invested", field: "totalInvestment", flex: 1, minWidth: 115, valueFormatter: p => formatCurrency(p.value), defaultVisible: true },
        { id: "totalCurrentValue", headerName: "Current", field: "totalCurrentValue", flex: 1, minWidth: 115, valueFormatter: p => formatCurrency(p.value), defaultVisible: true },
        { id: "profitLoss", headerName: "Profit / Loss", field: "profitLoss", flex: 1, minWidth: 115, sortable: true, valueFormatter: p => p.value?.toFixed(2), cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }), defaultVisible: true },
        { id: "absPNLPercentage", headerName: "Abs PNL%", field: "absPNLPercentage", flex: 1, minWidth: 95, sortable: true, valueFormatter: p => p.value != null ? `${Number(p.value).toFixed(2)}%` : "", cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }), defaultVisible: false },
        { id: "cagr", headerName: "CAGR", field: "cagr", flex: 1, minWidth: 95, sortable: true, valueFormatter: p => p.value != null ? `${Number(p.value).toFixed(2)}%` : "", cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }), defaultVisible: false },
        { id: "xirr", headerName: "XIRR", field: "xirr", flex: 1, minWidth: 95, sortable: true, valueFormatter: p => p.value != null ? `${Number(p.value).toFixed(2)}%` : "", defaultVisible: true },
        { id: "PNL1D", headerName: "DTD", field: "PNL1D", flex: 1, minWidth: 95, sortable: true, valueFormatter: p => p.value?.toFixed(2), cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }), defaultVisible: true },
        { id: "dtdPct", headerName: "DTD%", colId: "dtdPct", flex: 1, minWidth: 95, sortable: true, sort: "desc", valueGetter: p => (p.data.PNL1D && p.data.totalCurrentValue) ? (p.data.PNL1D / (p.data.totalCurrentValue - p.data.PNL1D)) * 100 : 0, valueFormatter: p => `${p.value.toFixed(2)}%`, cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }), defaultVisible: true },
        { id: "PNL1M", headerName: "MTD", field: "PNL1M", flex: 1, minWidth: 95, sortable: true, valueFormatter: p => p.value?.toFixed(2), cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }), defaultVisible: false },
        { id: "PNL1Y", headerName: "YTD", field: "PNL1Y", flex: 1, minWidth: 95, sortable: true, valueFormatter: p => p.value?.toFixed(2), cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }), defaultVisible: true },
        { id: "ltcg", headerName: "LTCG", field: "ltcg", flex: 1, minWidth: 100, sortable: true, valueFormatter: p => p.value?.toFixed(2), cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }), defaultVisible: false },
        { id: "stcg", headerName: "STCG", field: "stcg", flex: 1, minWidth: 100, sortable: true, valueFormatter: p => p.value?.toFixed(2), cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }), defaultVisible: false }
    ], []);

    // Column visibility preferences
    const [visibleCols, setVisibleCols] = useState(() => {
        const saved = localStorage.getItem("mf_visible_columns");
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                console.error("Error parsing saved columns", e);
            }
        }
        return {
            name: true,
            mutualFundNAV: true,
            averageNav: false,
            totalUnits: false,
            totalInvestment: true,
            totalCurrentValue: true,
            profitLoss: true,
            absPNLPercentage: false,
            cagr: false,
            xirr: true,
            PNL1D: true,
            dtdPct: true,
            PNL1M: false,
            PNL1Y: true,
            ltcg: false,
            stcg: false
        };
    });

    const [showColPicker, setShowColPicker] = useState(false);
    const [colSearchQuery, setColSearchQuery] = useState("");
    const [quickFilterText, setQuickFilterText] = useState("");
    const colPickerRef = useRef(null);

    // Toggle single column
    const toggleColumn = (colId) => {
        setVisibleCols(prev => {
            const updated = { ...prev, [colId]: !prev[colId] };
            localStorage.setItem("mf_visible_columns", JSON.stringify(updated));
            return updated;
        });
    };

    // Bulk selection helpers
    const selectAllColumns = () => {
        const all = {};
        ALL_MF_COLUMNS.forEach(col => { all[col.id] = true; });
        setVisibleCols(all);
        localStorage.setItem("mf_visible_columns", JSON.stringify(all));
    };

    const deselectAllColumns = () => {
        const none = { name: true }; // Keep Fund Name
        ALL_MF_COLUMNS.forEach(col => { if (col.id !== "name") none[col.id] = false; });
        setVisibleCols(none);
        localStorage.setItem("mf_visible_columns", JSON.stringify(none));
    };

    const resetDefaultColumns = () => {
        const defaults = {};
        ALL_MF_COLUMNS.forEach(col => { defaults[col.id] = col.defaultVisible; });
        setVisibleCols(defaults);
        localStorage.setItem("mf_visible_columns", JSON.stringify(defaults));
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

    // Active column definitions filtered by visibleCols
    const columnDefs = useMemo(() => {
        return ALL_MF_COLUMNS.filter(col => visibleCols[col.id]);
    }, [ALL_MF_COLUMNS, visibleCols]);

    const defaultColDef = useMemo(() => ({
        sortable: true, filter: true, resizable: true, flex: 1
    }), []);

    const investmentColDefs = [
        { headerName: "Date", field: "transactDate", flex: 1, sort: "desc", valueFormatter: p => p.value ? new Date(p.value.replace(" ", "T")).toLocaleDateString("en-CA") : "" },
        { headerName: "Type", field: "transactType", flex: 1 },
        { headerName: "Invested", field: "investValue", flex: 1, valueFormatter: p => p.value?.toFixed(2) },
        { headerName: "Units", field: "units", flex: 1, valueFormatter: p => p.value?.toFixed(2) },
        { headerName: "Buy NAV", field: "nav", flex: 1, valueFormatter: p => p.value?.toFixed(2) },
        { headerName: "Current NAV", field: "currentNAV", flex: 1, valueFormatter: p => p.value?.toFixed(2) },
        { headerName: "Current Value", field: "currentValue", flex: 1, valueFormatter: p => p.value?.toFixed(2) },
        { headerName: "Holding Days", field: "holdingDays", flex: 1 },
        { headerName: "P/L", field: "profitLoss", flex: 1, valueFormatter: p => p.value?.toFixed(2), cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }) },
        { headerName: "Abs%", field: "absPNLPercentange", flex: 1, valueFormatter: p => p.value != null ? `${p.value.toFixed(2)}%` : "", cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }) },
        { headerName: "CAGR%", field: "cagr", flex: 1, valueFormatter: p => p.value != null ? `${p.value.toFixed(2)}%` : "", cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }) },
        { headerName: "Taxation", field: "taxation", flex: 1 }
    ];

    // --- CUSTOM TOOLTIP FOR CHART ---
    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="custom-tooltip">
                    <p className="tooltip-date">{new Date(label).toLocaleDateString('en-IN')}</p>
                    <p className="tooltip-val">Value: <span>{formatCurrency(payload[0].value)}</span></p>
                    <p className="tooltip-inv">Invested: <span>{formatCurrency(payload[1].value)}</span></p>
                </div>
            );
        }
        return null;
    };

    if (error) return <div className="error-state">{error}</div>;
    if (loading) return (
        <div className="loading-container">
            <div className="financial-loader">
                <div className="bar"></div><div className="bar"></div><div className="bar"></div><div className="bar"></div><div className="bar"></div>
            </div>
            <h3 className="loading-text">Analyzing Portfolio...</h3>
            <p className="loading-subtext">Fetching latest NAV and Market Values</p>
        </div>
    );

    return (
        <div className="mf-dashboard">
            {/* 1. Header Section */}
            <header className="mf-header">
                <h1>Mutual Funds Overview</h1>
                <div className="date-filters">
                    <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
                    <span className="separator">to</span>
                    <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
                </div>
            </header>

            {/* 2. Stat Cards (Updated Layout) */}
            <section className="stats-grid">
                <div className="stat-card">
                    <div className="card-icon" style={{background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6'}}>💰</div>
                    <div className="info">
                        <h3>Invested Amount</h3>
                        <p>₹ {formatINR(summary.invested)}</p>
                    </div>
                </div>
                
                <div className="stat-card">
                    <div className="card-icon" style={{background: 'rgba(16, 185, 129, 0.1)', color: '#10b981'}}>📈</div>
                    <div className="info">
                        <h3>Current Value</h3>
                        <p>₹ {formatINR(summary.current)}</p>
                    </div>
                </div>

                <div className={`stat-card ${summary.unrealised >= 0 ? 'positive' : 'negative'}`} 
    style={{ display: 'flex', padding: 0, alignItems: 'stretch' }}>
    
    {/* LEFT SIDE: Reduced padding-right and flex-grow to pull the line in */}
    <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        padding: '1rem 0.5rem 1rem 1rem', // Reduced right padding from 1rem to 0.5rem
        flex: '0 1 auto', // Don't force growth, stay compact
        gap: '12px' 
    }}>
        <div className="card-icon" style={{background: summary.unrealised >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: summary.unrealised >= 0 ? '#10b981' : '#ef4444'}}>
            {summary.unrealised >= 0 ? '🚀' : '🔻'}
        </div>
        <div className="info">
            <h3 style={{ margin: 0 }}>Total P&L</h3>
            <div className="value-row" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <p style={{ margin: 0 }}>₹ {formatINR(Math.abs(summary.unrealised))}</p>
                <span className="badge" style={{ whiteSpace: 'nowrap' }}>{summary.unrealisedPct.toFixed(2)}%</span>
            </div>
        </div>
    </div>

    {/* THE PARTITION */}
    <div style={{ width: '1px', background: 'rgba(0,0,0,0.1)', margin: '12px 0' }}></div>

    {/* RIGHT SIDE: Set to flex: 1 to take up the remaining space */}
    <div style={{ flex: '1', display: 'flex', flexDirection: 'column' }}>
        {/* 1st Quadrant (LTCG) */}
        <div style={{ flex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 1rem', borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
            <span style={{ fontSize: '15px', fontWeight: '600', opacity: 0.8 }}>LTCG</span>
            <span style={{ fontSize: '16px', fontWeight: '600', color: summary.ltcg >= 0 ? '#10b981' : '#ef4444' }}>
                ₹{formatINR(Math.abs(summary.ltcg))}
            </span>
        </div>
        {/* 2nd Quadrant (STCG) */}
        <div style={{ flex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 1rem' }}>
            <span style={{ fontSize: '15px', fontWeight: '600', opacity: 0.8 }}>STCG</span>
            <span style={{ fontSize: '16px', fontWeight: '600', color: summary.stcg >= 0 ? '#10b981' : '#ef4444' }}>
                ₹{formatINR(Math.abs(summary.stcg))}
            </span>
        </div>
    </div>
</div>

                <div className={`stat-card ${summary.today >= 0 ? 'positive' : 'negative'}`}>
                    <div className="card-icon" style={{background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b'}}>📅</div>
                    <div className="info">
                        <h3>Today's Change</h3>
                        <div className="value-row">
                            <p>₹ {formatINR(Math.abs(summary.today))}</p>
                            <span className="badge">{summary.todayPct.toFixed(2)}%</span>
                        </div>
                    </div>
                </div>
            </section>

            {/* 3. Main Content - Stacked Layout */}
            <div className="content-split">
                
                {/* --- TOP: MASTER GRID --- */}
                <div className="grid-container">
                    <div className="grid-header-row">
                        <div className="grid-header-title">
                            <h3>My Holdings</h3>
                            <span className="holdings-count-badge">{mutualFundData.length} Funds</span>
                        </div>

                        <div className="grid-header-controls">
                            {/* Quick Search */}
                            <div className="table-search-box">
                                <span className="search-icon">🔍</span>
                                <input 
                                    type="text" 
                                    placeholder="Search funds..." 
                                    value={quickFilterText} 
                                    onChange={e => setQuickFilterText(e.target.value)} 
                                />
                            </div>

                            {/* Column Chooser Button & Popover */}
                            <div className="col-picker-container" ref={colPickerRef}>
                                <button 
                                    className={`col-picker-btn ${showColPicker ? 'active' : ''}`}
                                    onClick={() => setShowColPicker(!showColPicker)}
                                    title="Customize Visible Columns"
                                >
                                    <span>⚙️</span>
                                    <span>Columns</span>
                                    <span className="col-count-chip">
                                        {Object.values(visibleCols).filter(Boolean).length}/{ALL_MF_COLUMNS.length}
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
                                            {ALL_MF_COLUMNS
                                                .filter(col => col.headerName.toLowerCase().includes(colSearchQuery.toLowerCase()))
                                                .map(col => (
                                                    <label key={col.id} className="col-checkbox-label">
                                                        <input 
                                                            type="checkbox" 
                                                            checked={!!visibleCols[col.id]} 
                                                            onChange={() => toggleColumn(col.id)} 
                                                            disabled={col.id === 'name'} 
                                                        />
                                                        <span className="col-name-text">{col.headerName}</span>
                                                        {col.defaultVisible && <span className="default-pill">Default</span>}
                                                    </label>
                                                ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="ag-theme-alpine" style={{ flex: 1, width: '100%' }}>
                        <AgGridReact
                            rowData={mutualFundData}
                            columnDefs={columnDefs}
                            defaultColDef={defaultColDef}
                            pagination={true}
                            paginationPageSize={20} 
                            quickFilterText={quickFilterText}
                            onRowDoubleClicked={(e) => { setSelectedFund(e.data); setModalOpen(true); }}
                            rowSelection="single"
                            animateRows={true}
                        />
                    </div>
                    <div className="grid-hint">Double click a row to view detailed transactions</div>
                </div>

                {/* --- BOTTOM: CHART --- */}
                <div className="chart-container">
                    <h3>Portfolio Growth Trend</h3>
                    <ResponsiveContainer width="100%" height={350}>
                        <AreaChart data={filteredChartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8}/>
                                    <stop offset="95%" stopColor="#82ca9d" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                            <XAxis 
                                dataKey="date" 
                                tickFormatter={d => new Date(d).toLocaleDateString('en-IN', {month:'short', year:'2-digit'})} 
                                minTickGap={30} 
                                axisLine={false} 
                                tickLine={false} 
                            />
                            <YAxis hide domain={['auto', 'auto']} />
                            <Tooltip content={<CustomTooltip />} />
                            <Area 
                                type="monotone" 
                                dataKey="value" 
                                stroke="#82ca9d" 
                                fillOpacity={1} 
                                fill="url(#colorValue)" 
                                strokeWidth={2} 
                            />
                            <Area 
                                type="monotone" 
                                dataKey="invested" 
                                stroke="#8884d8" 
                                fill="transparent" 
                                strokeDasharray="5 5" 
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* 4. Modal Overlay */}
            {modalOpen && selectedFund && (
                <div className="modal-backdrop" onClick={() => setModalOpen(false)}>
                    <div className="modal-panel" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <h2>{selectedFund.name}</h2>
                                <span className="modal-subtitle">{selectedFund.numInvestments} Transactions Found</span>
                            </div>
                            <button className="close-btn" onClick={() => setModalOpen(false)}>×</button>
                        </div>
                        <div className="modal-grid ag-theme-alpine">
                            <AgGridReact
                                rowData={selectedFund.investments}
                                columnDefs={investmentColDefs}
                                defaultColDef={defaultColDef}
                                animateRows={true}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MutualFund;