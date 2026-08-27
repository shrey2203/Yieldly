import { 
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from "recharts";
import { AgGridReact } from "ag-grid-react";
import { useState, useEffect, useMemo } from "react";
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
        todayPct: 0
    });

    const [mutualFundData, setMutualFundData] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [filteredChartData, setFilteredChartData] = useState([]);

    // Filters & UI State
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedFund, setSelectedFund] = useState(null);

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
                todayPct: (data.todayPNL * 100) / data.totalCurrentSum
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

    // --- AG GRID DEFINITIONS ---
    const defaultColDef = useMemo(() => ({
        sortable: true, filter: true, resizable: true, flex: 1
    }), []);

    const columnDefs = [
        { headerName: "Fund Name", field: "name", flex: 2, sortable: true, filter: true },
        { headerName: "NAV", field: "mutualFundNAV", flex: 1, sortable: true, valueFormatter: p => (p.value ? Number(p.value).toFixed(2) : "") },
        // { headerName: "Average NAV", field: "averageNav", flex: 1, sortable: true, valueFormatter: p => (p.value ? Number(p.value).toFixed(2) : "") },
        // { headerName: "Total Units", field: "totalUnits", flex: 1, sortable: true, valueFormatter: p => (p.value ? Number(p.value).toFixed(2) : "") },
        { headerName: "Invested", field: "totalInvestment", valueFormatter: p => formatCurrency(p.value)},
        { headerName: "Current", field: "totalCurrentValue", valueFormatter: p => formatCurrency(p.value)},
        { headerName: "Profit / Loss", field: "profitLoss", flex: 1, sortable: true, valueFormatter: p => p.value?.toFixed(2), cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }) },
        // { headerName: "Abs PNL%", field: "absPNLPercentage", flex: 1, sortable: true, valueFormatter: p => p.value != null ? `${Number(p.value).toFixed(2)}%` : "" },
        { headerName: "CAGR", field: "cagr", flex: 1, sortable: true, valueFormatter: p => p.value != null ? `${Number(p.value).toFixed(2)}%` : "" },
        { headerName: "XIRR", field: "xirr", flex: 1, sortable: true, valueFormatter: p => p.value != null ? `${Number(p.value).toFixed(2)}%` : "" },
        { headerName: "DTD", field: "PNL1D", flex: 1, sortable: true, sort: "desc", valueFormatter: p => p.value?.toFixed(2), cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }) },
        { headerName: "MTD", field: "PNL1M", flex: 1, sortable: true, valueFormatter: p => p.value?.toFixed(2), cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }) },
        { headerName: "YTD", field: "PNL1Y", flex: 1, sortable: true, valueFormatter: p => p.value?.toFixed(2), cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }) }
    ];

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
        { headerName: "CAGR%", field: "cagr", flex: 1, valueFormatter: p => p.value != null ? `${p.value.toFixed(2)}%` : "", cellStyle: p => ({ color: p.value < 0 ? "red" : "green", fontWeight: "bold" }) }
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

                <div className={`stat-card ${summary.unrealised >= 0 ? 'positive' : 'negative'}`}>
                    <div className="card-icon" style={{background: summary.unrealised >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: summary.unrealised >= 0 ? '#10b981' : '#ef4444'}}>
                        {summary.unrealised >= 0 ? '🚀' : '🔻'}
                    </div>
                    <div className="info">
                        <h3>Total P&L</h3>
                        <div className="value-row">
                            <p>₹ {formatINR(Math.abs(summary.unrealised))}</p>
                            <span className="badge">{summary.unrealisedPct.toFixed(2)}%</span>
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
                    <h3>My Holdings</h3>
                    <div className="ag-theme-alpine" style={{ flex: 1, width: '100%' }}>
                        <AgGridReact
                            rowData={mutualFundData}
                            columnDefs={columnDefs}
                            defaultColDef={defaultColDef}
                            pagination={true}
                            paginationPageSize={20} 
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