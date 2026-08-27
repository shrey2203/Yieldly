import { AgGridReact } from "ag-grid-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const AnalysisUI = ({ loading, summary, analysisData, columnDefs, searchQuery, setSearchQuery, handleSearch, gridRef }) => (
    <div className="mf-dashboard">
        {/* 1. Header Section - Matching MF Style */}
        <header className="mf-header">
            <h1>Institutional Analysis</h1>
            <div className="date-filters">
                <input 
                    type="text" 
                    placeholder="Search Scrip..." 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    style={{ padding: "8px", borderRadius: "4px", border: "1px solid #ddd" }}
                />
                <button className="execute-btn" onClick={handleSearch} style={{ marginLeft: "10px" }}>
                    {loading ? "..." : "Analyze"}
                </button>
            </div>
        </header>

        {/* 2. Stat Cards - Matching MF Style */}
        <section className="stats-grid">
            <div className="stat-card">
                <div className="card-icon" style={{background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6'}}>📊</div>
                <div className="info">
                    <h3>Tracked Stocks</h3>
                    <p>{summary.totalStocks}</p>
                </div>
            </div>
            
            <div className="stat-card">
                <div className="card-icon" style={{background: 'rgba(16, 185, 129, 0.1)', color: '#10b981'}}>🏛️</div>
                <div className="info">
                    <h3>Avg FII Holding</h3>
                    <p>{summary.avgFii}%</p>
                </div>
            </div>

            <div className="stat-card">
                <div className="card-icon" style={{background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b'}}>🏢</div>
                <div className="info">
                    <h3>Avg DII Holding</h3>
                    <p>{summary.avgDii}%</p>
                </div>
            </div>

            <div className="stat-card positive">
                <div className="card-icon" style={{background: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6'}}>👑</div>
                <div className="info">
                    <h3>Top FII Pick</h3>
                    <p>{summary.topGainer}</p>
                </div>
            </div>
        </section>

        {/* 3. Content Split - Grid Top / Chart Bottom */}
        <div className="content-split">
            
            <div className="grid-container">
                <h3>Institutional Ownership Table</h3>
                <div className="ag-theme-alpine" style={{ height: "400px", width: '100%' }}>
                    <AgGridReact
                        ref={gridRef}
                        rowData={analysisData}
                        columnDefs={columnDefs}
                        defaultColDef={{ flex: 1, sortable: true, filter: true, resizable: true }}
                        pagination={true}
                        paginationPageSize={10}
                        animateRows={true}
                    />
                </div>
            </div>

            <div className="chart-container" style={{ marginTop: "20px" }}>
                <h3>FII Concentration Trend (Selection)</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={analysisData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorFii" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                        <XAxis dataKey="stock" axisLine={false} tickLine={false} />
                        <YAxis hide />
                        <Tooltip />
                        <Area type="monotone" dataKey="fiiHolding" stroke="#3b82f6" fillOpacity={1} fill="url(#colorFii)" />
                        <Area type="monotone" dataKey="diiHolding" stroke="#f59e0b" fill="transparent" strokeDasharray="5 5" />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    </div>
);

export default AnalysisUI;

