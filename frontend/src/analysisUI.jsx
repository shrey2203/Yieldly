import { AgGridReact } from "ag-grid-react";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

const AnalysisUI = ({ 
    loading, 
    summary, 
    analysisData, 
    selectedStock, 
    columnDefs, 
    searchQuery, 
    setSearchQuery, 
    handleSearch, 
    handleClearAll,
    handleRowClick, 
    gridRef 
}) => {
    const epsChartData = selectedStock?.quarterlyEps?.length > 0 
        ? selectedStock.quarterlyEps.map(item => ({ quarter: item.quarter, eps: Number(item.eps) }))
        : (selectedStock?.epsLast4Qtrs?.length > 0 
            ? selectedStock.epsLast4Qtrs.map((val, idx) => ({ quarter: `Q${idx + 1}`, eps: Number(val) }))
            : []);

    const holdingChartData = selectedStock ? [
        { name: "Promoter", value: Number(selectedStock.promoterHolding) || 0, color: "#3b82f6" },
        { name: "FII", value: Number(selectedStock.fiiHolding) || 0, color: "#10b981" },
        { name: "DII", value: Number(selectedStock.diiHolding) || 0, color: "#f59e0b" },
        { name: "Public", value: Number(selectedStock.publicHolding) || 0, color: "#8b5cf6" },
    ].filter(item => item.value > 0) : [];

    return (
        <div className="mf-dashboard">
            {/* 1. Header Section */}
            <header className="mf-header">
                <div>
                    <h1 style={{ fontSize: "24px", fontWeight: "700", color: "#0f172a", margin: 0 }}>
                        Stock Fundamental & Technical Analysis
                    </h1>
                    <p style={{ margin: "4px 0 0 0", color: "#64748b", fontSize: "13px" }}>
                        Inspect P/E, Quarterly EPS, Institutional Shifts, RSI momentum, and Debt-to-Equity
                    </p>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div className="date-filters" style={{ display: "flex", alignItems: "center", gap: "10px", background: "white", padding: "6px 12px", borderRadius: "8px", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
                        <input 
                            type="text" 
                            placeholder="Search Scrip (e.g. RELIANCE, TCS)..." 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                            style={{ 
                                padding: "8px 12px", 
                                borderRadius: "6px", 
                                border: "1px solid #cbd5e1",
                                fontSize: "14px",
                                outline: "none",
                                width: "250px"
                            }}
                        />
                        <button 
                            className="execute-btn" 
                            onClick={handleSearch} 
                            disabled={loading}
                            style={{ 
                                padding: "8px 18px", 
                                background: "#0284c7", 
                                color: "white", 
                                border: "none", 
                                borderRadius: "6px", 
                                fontWeight: "600",
                                cursor: loading ? "not-allowed" : "pointer",
                                fontSize: "14px",
                                transition: "background 0.2s"
                            }}
                        >
                            {loading ? "Analyzing..." : "Analyze"}
                        </button>
                    </div>

                    {analysisData && analysisData.length > 0 && (
                        <button
                            onClick={handleClearAll}
                            title="Clear all analyzed stocks in session"
                            style={{
                                padding: "8px 14px",
                                background: "#f8fafc",
                                border: "1px solid #e2e8f0",
                                borderRadius: "8px",
                                color: "#64748b",
                                fontSize: "13px",
                                fontWeight: "600",
                                cursor: "pointer",
                                transition: "all 0.15s ease"
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.color = "#ef4444";
                                e.currentTarget.style.borderColor = "#fca5a5";
                                e.currentTarget.style.background = "#fff5f5";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.color = "#64748b";
                                e.currentTarget.style.borderColor = "#e2e8f0";
                                e.currentTarget.style.background = "#f8fafc";
                            }}
                        >
                            Clear All
                        </button>
                    )}
                </div>
            </header>

            {/* 2. Stat Cards */}
            <section className="stats-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px", marginBottom: "20px" }}>
                <div className="stat-card" style={{ background: "white", padding: "18px", borderRadius: "10px", display: "flex", alignItems: "center", gap: "14px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                    <div style={{ width: "42px", height: "42px", borderRadius: "8px", background: "rgba(59, 130, 246, 0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "20px", color: "#3b82f6" }}>
                        📊
                    </div>
                    <div>
                        <h3 style={{ margin: 0, fontSize: "12px", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.5px" }}>Tracked Stocks</h3>
                        <p style={{ margin: "4px 0 0 0", fontSize: "20px", fontWeight: "700", color: "#0f172a" }}>{summary.totalStocks}</p>
                    </div>
                </div>
                
                <div className="stat-card" style={{ background: "white", padding: "18px", borderRadius: "10px", display: "flex", alignItems: "center", gap: "14px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                    <div style={{ width: "42px", height: "42px", borderRadius: "8px", background: "rgba(16, 185, 129, 0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "20px", color: "#10b981" }}>
                        ⚖️
                    </div>
                    <div>
                        <h3 style={{ margin: 0, fontSize: "12px", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.5px" }}>Avg P/E Ratio</h3>
                        <p style={{ margin: "4px 0 0 0", fontSize: "20px", fontWeight: "700", color: "#0f172a" }}>{summary.avgPe}</p>
                    </div>
                </div>

                <div className="stat-card" style={{ background: "white", padding: "18px", borderRadius: "10px", display: "flex", alignItems: "center", gap: "14px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                    <div style={{ width: "42px", height: "42px", borderRadius: "8px", background: "rgba(245, 158, 11, 0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "20px", color: "#f59e0b" }}>
                        ⚡
                    </div>
                    <div>
                        <h3 style={{ margin: 0, fontSize: "12px", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.5px" }}>Avg RSI (14)</h3>
                        <p style={{ margin: "4px 0 0 0", fontSize: "20px", fontWeight: "700", color: "#0f172a" }}>{summary.avgRsi}</p>
                    </div>
                </div>

                <div className="stat-card" style={{ background: "white", padding: "18px", borderRadius: "10px", display: "flex", alignItems: "center", gap: "14px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                    <div style={{ width: "42px", height: "42px", borderRadius: "8px", background: "rgba(139, 92, 246, 0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "20px", color: "#8b5cf6" }}>
                        🏛️
                    </div>
                    <div>
                        <h3 style={{ margin: 0, fontSize: "12px", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.5px" }}>Top FII Pick</h3>
                        <p style={{ margin: "4px 0 0 0", fontSize: "20px", fontWeight: "700", color: "#0f172a" }}>{summary.topFii}</p>
                    </div>
                </div>
            </section>

            {/* 3. Main Content Split: AG Grid Table on Top */}
            <div className="content-split" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                
                <div className="grid-container" style={{ background: "white", padding: "20px", borderRadius: "12px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                        <div>
                            <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "700", color: "#1e293b" }}>
                                Analyzed Stocks Matrix
                            </h3>
                            <span style={{ fontSize: "12px", color: "#64748b" }}>
                                Cached for your active session • Click any row to inspect deep-dive charts
                            </span>
                        </div>
                    </div>

                    <div className="ag-theme-alpine" style={{ height: "380px", width: "100%" }}>
                        <AgGridReact
                            ref={gridRef}
                            rowData={analysisData}
                            columnDefs={columnDefs}
                            defaultColDef={{ 
                                flex: 1, 
                                sortable: true, 
                                filter: true, 
                                resizable: true,
                                cellStyle: { display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center" }
                            }}
                            pagination={true}
                            paginationPageSize={10}
                            animateRows={true}
                            onRowClicked={handleRowClick}
                            rowSelection="single"
                            overlayNoRowsTemplate="<span style='color: #64748b; font-size: 14px;'>No stocks analyzed yet. Enter a scrip name above and click Analyze!</span>"
                        />
                    </div>
                </div>

                {/* 4. Selected Stock Deep-Dive Analytics */}
                {selectedStock && (
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                        {/* Quarterly EPS Trend */}
                        <div style={{ background: "white", padding: "20px", borderRadius: "12px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                                <div>
                                    <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "700", color: "#0f172a" }}>
                                        {selectedStock.stock} — Last 4 Quarters EPS Trend
                                    </h3>
                                    <p style={{ margin: "2px 0 0 0", color: "#64748b", fontSize: "12px" }}>Earnings Per Share (₹ / share)</p>
                                </div>
                                {/* Current PE + median comparison badges */}
                                <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                                    <span style={{ background: "#f1f5f9", padding: "4px 10px", borderRadius: "6px", fontSize: "12px", fontWeight: "700", color: "#0284c7" }}>
                                        P/E: {selectedStock.peRatio ? `${selectedStock.peRatio}x` : "—"}
                                    </span>
                                    {selectedStock.peMedian1Y != null && (
                                        <span title={`1Y Median: ${selectedStock.peMedian1Y}x | ${selectedStock.belowMedian1Y ? "Trading below — historically cheap" : "Trading above — historically rich"}`}
                                            style={{ 
                                                padding: "4px 8px", borderRadius: "6px", fontSize: "11px", fontWeight: "700",
                                                background: selectedStock.belowMedian1Y ? "#dcfce7" : "#fee2e2",
                                                color: selectedStock.belowMedian1Y ? "#15803d" : "#b91c1c"
                                            }}>
                                            1Y med {selectedStock.belowMedian1Y ? "↓" : "↑"} {selectedStock.peMedian1Y}x
                                        </span>
                                    )}
                                    {selectedStock.peMedian3Y != null && (
                                        <span title={`3Y Median: ${selectedStock.peMedian3Y}x | ${selectedStock.belowMedian3Y ? "Trading below — historically cheap" : "Trading above — historically rich"}`}
                                            style={{ 
                                                padding: "4px 8px", borderRadius: "6px", fontSize: "11px", fontWeight: "700",
                                                background: selectedStock.belowMedian3Y ? "#dcfce7" : "#fee2e2",
                                                color: selectedStock.belowMedian3Y ? "#15803d" : "#b91c1c"
                                            }}>
                                            3Y med {selectedStock.belowMedian3Y ? "↓" : "↑"} {selectedStock.peMedian3Y}x
                                        </span>
                                    )}
                                    {selectedStock.peMedian5Y != null && (
                                        <span title={`5Y Median: ${selectedStock.peMedian5Y}x | ${selectedStock.belowMedian5Y ? "Trading below — historically cheap" : "Trading above — historically rich"}`}
                                            style={{ 
                                                padding: "4px 8px", borderRadius: "6px", fontSize: "11px", fontWeight: "700",
                                                background: selectedStock.belowMedian5Y ? "#dcfce7" : "#fee2e2",
                                                color: selectedStock.belowMedian5Y ? "#15803d" : "#b91c1c"
                                            }}>
                                            5Y med {selectedStock.belowMedian5Y ? "↓" : "↑"} {selectedStock.peMedian5Y}x
                                        </span>
                                    )}
                                </div>
                            </div>

                            {epsChartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={240}>
                                    <BarChart data={epsChartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                        <XAxis dataKey="quarter" stroke="#64748b" fontSize={12} tickLine={false} />
                                        <YAxis stroke="#64748b" fontSize={12} tickLine={false} />
                                        <Tooltip 
                                            formatter={(val) => [`₹${val}`, "EPS"]}
                                            contentStyle={{ borderRadius: "8px", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)" }}
                                        />
                                        <Bar dataKey="eps" fill="#0284c7" radius={[6, 6, 0, 0]}>
                                            {epsChartData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={index === epsChartData.length - 1 ? "#0284c7" : "#93c5fd"} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div style={{ height: "240px", display: "flex", alignItems: "center", justifyContent: "center", color: "#94a3b8" }}>
                                    No quarterly EPS data available for {selectedStock.stock}
                                </div>
                            )}
                        </div>

                        {/* Shareholding Breakdown & Key Metrics */}
                        <div style={{ background: "white", padding: "20px", borderRadius: "12px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                                <div>
                                    <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "700", color: "#0f172a" }}>
                                        {selectedStock.stock} — Ownership Distribution
                                    </h3>
                                    <p style={{ margin: "2px 0 0 0", color: "#64748b", fontSize: "12px" }}>Promoter vs Institutional vs Public</p>
                                </div>
                                <span style={{ background: selectedStock.debtToEquity <= 0.5 ? "#dcfce7" : "#fee2e2", color: selectedStock.debtToEquity <= 0.5 ? "#15803d" : "#b91c1c", padding: "4px 10px", borderRadius: "6px", fontSize: "12px", fontWeight: "700" }}>
                                    D/E: {selectedStock.debtToEquity !== null && selectedStock.debtToEquity !== undefined ? selectedStock.debtToEquity : "—"}
                                </span>
                            </div>

                            {holdingChartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={240}>
                                    <BarChart data={holdingChartData} layout="vertical" margin={{ top: 10, right: 30, left: 20, bottom: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                                        <XAxis type="number" unit="%" stroke="#64748b" fontSize={12} tickLine={false} />
                                        <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
                                        <Tooltip 
                                            formatter={(val) => [`${val}%`, "Holding"]}
                                            contentStyle={{ borderRadius: "8px", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)" }}
                                        />
                                        <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                                            {holdingChartData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div style={{ height: "240px", display: "flex", alignItems: "center", justifyContent: "center", color: "#94a3b8" }}>
                                    No shareholding pattern available for {selectedStock.stock}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AnalysisUI;
