import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { ModuleRegistry, ClientSideRowModelModule, AllCommunityModule } from "ag-grid-community";
import AnalysisUI from "./analysisUI"; 
import "./analysis.css";

ModuleRegistry.registerModules([ClientSideRowModelModule, AllCommunityModule]);

const Analysis = () => {
    const rawUser = (localStorage.getItem("username") || "USER").toUpperCase();
    const STORAGE_KEY = `yieldly_stock_analysis_${rawUser}`;

    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    
    // Initialize analysisData from sessionStorage so navigation across tabs/pages preserves it
    const [analysisData, setAnalysisData] = useState(() => {
        try {
            const cached = sessionStorage.getItem(STORAGE_KEY);
            return cached ? JSON.parse(cached) : [];
        } catch (err) {
            console.error("Error reading cached stock analysis:", err);
            return [];
        }
    });

    const [selectedStock, setSelectedStock] = useState(() => {
        try {
            const cached = sessionStorage.getItem(STORAGE_KEY);
            const parsed = cached ? JSON.parse(cached) : [];
            return parsed.length > 0 ? parsed[0] : null;
        } catch (e) {
            return null;
        }
    });
    
    const [summary, setSummary] = useState({
        totalStocks: 0,
        avgPe: "—",
        avgRsi: "—",
        topFii: "—"
    });

    const gridRef = useRef();

    // Persist analysisData to sessionStorage on any change
    useEffect(() => {
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(analysisData));
        } catch (err) {
            console.error("Error saving stock analysis to sessionStorage:", err);
        }
    }, [analysisData, STORAGE_KEY]);

    // Recalculate summary stats
    useEffect(() => {
        if (analysisData.length > 0) {
            const validPe = analysisData.filter(d => Number(d.peRatio) > 0);
            const avgPe = validPe.length > 0
                ? (validPe.reduce((acc, curr) => acc + Number(curr.peRatio), 0) / validPe.length).toFixed(1)
                : "—";

            const validRsi = analysisData.filter(d => Number(d.rsi) > 0);
            const avgRsi = validRsi.length > 0
                ? (validRsi.reduce((acc, curr) => acc + Number(curr.rsi), 0) / validRsi.length).toFixed(1)
                : "—";

            const topFiiStock = [...analysisData].sort((a, b) => (Number(b.fiiHolding) || 0) - (Number(a.fiiHolding) || 0))[0];

            setSummary({
                totalStocks: analysisData.length,
                avgPe: avgPe !== "—" ? `${avgPe}x` : "—",
                avgRsi: avgRsi,
                topFii: topFiiStock ? topFiiStock.stock : "—"
            });

            // Ensure selectedStock points to an existing item
            if (!selectedStock || !analysisData.some(d => d.stock === selectedStock.stock)) {
                setSelectedStock(analysisData[0]);
            }
        } else {
            setSummary({
                totalStocks: 0,
                avgPe: "—",
                avgRsi: "—",
                topFii: "—"
            });
            setSelectedStock(null);
        }
    }, [analysisData, selectedStock]);

    // Delete single stock
    const handleDeleteStock = useCallback((stockSymbol) => {
        setAnalysisData(prev => {
            const updated = prev.filter(item => item.stock !== stockSymbol);
            if (selectedStock?.stock === stockSymbol) {
                setSelectedStock(updated.length > 0 ? updated[0] : null);
            }
            return updated;
        });
    }, [selectedStock]);

    // Clear all analyzed stocks
    const handleClearAll = useCallback(() => {
        setAnalysisData([]);
        setSelectedStock(null);
        try {
            sessionStorage.removeItem(STORAGE_KEY);
        } catch (e) {}
    }, [STORAGE_KEY]);

    const columnDefs = useMemo(() => [
        { 
            headerName: "Scrip", 
            field: "stock", 
            flex: 1.4,
            pinned: "left",
            cellRenderer: p => (
                <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", lineHeight: "1.3" }}>
                    <span style={{ fontWeight: "700", color: "#0f172a" }}>{p.value}</span>
                    {p.data?.companyName && p.data.companyName !== p.value && (
                        <span style={{ fontSize: "11px", color: "#64748b", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                            {p.data.companyName}
                        </span>
                    )}
                </div>
            )
        },
        { 
            headerName: "P/E vs Medians", 
            field: "peRatio", 
            flex: 2.0,
            cellRenderer: p => {
                const pe = p.value !== null && p.value !== undefined ? Number(p.value) : null;
                if (pe === null) return <span style={{ color: "#94a3b8" }}>—</span>;

                const m1y = p.data?.peMedian1Y;
                const m3y = p.data?.peMedian3Y;
                const m5y = p.data?.peMedian5Y;
                const b1y = p.data?.belowMedian1Y;
                const b3y = p.data?.belowMedian3Y;
                const b5y = p.data?.belowMedian5Y;

                return (
                    <div style={{ display: "flex", alignItems: "center", gap: "5px", flexWrap: "wrap", padding: "2px 0" }}>
                        <span style={{ fontWeight: "700", fontSize: "13px", color: "#0f172a", marginRight: "4px" }}>
                            {pe.toFixed(1)}x
                        </span>
                        {m1y != null && (
                            <span title={`1Y Median PE: ${m1y}x`} style={{ 
                                fontSize: "10px", fontWeight: "700", padding: "1px 5px", borderRadius: "4px",
                                background: b1y ? "#dcfce7" : "#fee2e2",
                                color: b1y ? "#15803d" : "#b91c1c"
                            }}>
                                1Y {b1y ? "↓" : "↑"} {m1y}x
                            </span>
                        )}
                        {m3y != null && (
                            <span title={`3Y Median PE: ${m3y}x`} style={{ 
                                fontSize: "10px", fontWeight: "700", padding: "1px 5px", borderRadius: "4px",
                                background: b3y ? "#dcfce7" : "#fee2e2",
                                color: b3y ? "#15803d" : "#b91c1c"
                            }}>
                                3Y {b3y ? "↓" : "↑"} {m3y}x
                            </span>
                        )}
                        {m5y != null && (
                            <span title={`5Y Median PE: ${m5y}x`} style={{ 
                                fontSize: "10px", fontWeight: "700", padding: "1px 5px", borderRadius: "4px",
                                background: b5y ? "#dcfce7" : "#fee2e2",
                                color: b5y ? "#15803d" : "#b91c1c"
                            }}>
                                5Y {b5y ? "↓" : "↑"} {m5y}x
                            </span>
                        )}
                    </div>
                );
            }
        },
        { 
            headerName: "Debt / Equity", 
            field: "debtToEquity", 
            flex: 0.9,
            valueFormatter: p => (p.value !== null && p.value !== undefined) ? Number(p.value).toFixed(2) : "—",
            cellStyle: p => {
                const val = Number(p.value);
                const color = isNaN(val) ? "#64748b" : (val <= 0.5 ? "#10b981" : (val <= 1.2 ? "#f59e0b" : "#ef4444"));
                return { fontWeight: "600", color, textAlign: "center" };
            }
        },
        { 
            headerName: "RSI (14)", 
            field: "rsi", 
            flex: 1.1,
            cellRenderer: p => {
                const val = Number(p.value);
                if (isNaN(val) || val === 0) return <span style={{ color: "#94a3b8" }}>—</span>;
                let bg = "#e0f2fe";
                let textCol = "#0369a1";
                let label = "Neutral";
                if (val >= 70) {
                    bg = "#fee2e2";
                    textCol = "#b91c1c";
                    label = "Overbought";
                } else if (val <= 30) {
                    bg = "#dcfce7";
                    textCol = "#15803d";
                    label = "Oversold";
                }
                return (
                    <div style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
                        <span style={{ 
                            background: bg, 
                            color: textCol, 
                            padding: "2px 8px", 
                            borderRadius: "12px", 
                            fontSize: "12px", 
                            fontWeight: "700" 
                        }}>
                            {val.toFixed(1)}
                        </span>
                        <span style={{ fontSize: "10px", color: "#64748b" }}>({label})</span>
                    </div>
                );
            }
        },
        { 
            headerName: "EPS Last 4 Qtrs", 
            field: "quarterlyEps", 
            flex: 2.1,
            cellRenderer: p => {
                const qEps = p.value || [];
                if (!qEps || qEps.length === 0) {
                    const last4 = p.data?.epsLast4Qtrs || [];
                    if (!last4 || last4.length === 0) return <span style={{ color: "#94a3b8" }}>—</span>;
                    return (
                        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                            {last4.map((val, idx) => (
                                <span key={idx} style={{ background: "#f1f5f9", padding: "2px 6px", borderRadius: "4px", fontSize: "11px", fontWeight: "600" }}>
                                    ₹{Number(val).toFixed(1)}
                                </span>
                            ))}
                        </div>
                    );
                }
                return (
                    <div style={{ display: "flex", gap: "5px", alignItems: "center", flexWrap: "nowrap", overflowX: "auto" }}>
                        {qEps.map((item, idx) => (
                            <span 
                                key={idx} 
                                title={`${item.quarter}: ₹${item.eps}`}
                                style={{ 
                                    background: "#f1f5f9", 
                                    color: "#334155", 
                                    padding: "2px 6px", 
                                    borderRadius: "4px", 
                                    fontSize: "11px", 
                                    fontWeight: "600",
                                    whiteSpace: "nowrap"
                                }}
                            >
                                <span style={{ color: "#94a3b8", fontSize: "9px", marginRight: "3px" }}>{item.quarter.slice(0, 3)}</span>
                                ₹{Number(item.eps).toFixed(1)}
                            </span>
                        ))}
                    </div>
                );
            }
        },
        { 
            headerName: "Promoter % (QoQ)", 
            field: "promoterHolding", 
            flex: 1.2,
            cellRenderer: p => {
                const val = p.value !== null && p.value !== undefined ? Number(p.value) : null;
                const change = p.data?.promoterChange !== null && p.data?.promoterChange !== undefined ? Number(p.data.promoterChange) : null;
                if (val === null) return <span style={{ color: "#94a3b8" }}>—</span>;
                return (
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}>
                        <span style={{ fontWeight: "600", color: "#1e293b" }}>{val.toFixed(2)}%</span>
                        {change !== null && (
                            <span style={{ 
                                fontSize: "11px", 
                                fontWeight: "700", 
                                color: change > 0 ? "#10b981" : (change < 0 ? "#ef4444" : "#94a3b8") 
                            }}>
                                {change > 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`}
                            </span>
                        )}
                    </div>
                );
            }
        },
        { 
            headerName: "FII % (QoQ)", 
            field: "fiiHolding", 
            flex: 1.2,
            cellRenderer: p => {
                const val = p.value !== null && p.value !== undefined ? Number(p.value) : null;
                const change = p.data?.fiiChange !== null && p.data?.fiiChange !== undefined ? Number(p.data.fiiChange) : null;
                if (val === null) return <span style={{ color: "#94a3b8" }}>—</span>;
                return (
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}>
                        <span style={{ fontWeight: "600", color: "#1e293b" }}>{val.toFixed(2)}%</span>
                        {change !== null && (
                            <span style={{ 
                                fontSize: "11px", 
                                fontWeight: "700", 
                                color: change > 0 ? "#10b981" : (change < 0 ? "#ef4444" : "#94a3b8") 
                            }}>
                                {change > 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`}
                            </span>
                        )}
                    </div>
                );
            }
        },
        { 
            headerName: "DII % (QoQ)", 
            field: "diiHolding", 
            flex: 1.2,
            cellRenderer: p => {
                const val = p.value !== null && p.value !== undefined ? Number(p.value) : null;
                const change = p.data?.diiChange !== null && p.data?.diiChange !== undefined ? Number(p.data.diiChange) : null;
                if (val === null) return <span style={{ color: "#94a3b8" }}>—</span>;
                return (
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}>
                        <span style={{ fontWeight: "600", color: "#1e293b" }}>{val.toFixed(2)}%</span>
                        {change !== null && (
                            <span style={{ 
                                fontSize: "11px", 
                                fontWeight: "700", 
                                color: change > 0 ? "#10b981" : (change < 0 ? "#ef4444" : "#94a3b8") 
                            }}>
                                {change > 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`}
                            </span>
                        )}
                    </div>
                );
            }
        },
        {
            headerName: "Action",
            field: "action",
            flex: 0.6,
            sortable: false,
            filter: false,
            pinned: "right",
            cellRenderer: p => (
                <button
                    title={`Delete ${p.data?.stock} from matrix`}
                    onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteStock(p.data?.stock);
                    }}
                    style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        fontSize: "14px",
                        color: "#94a3b8",
                        transition: "all 0.15s ease"
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.color = "#ef4444";
                        e.currentTarget.style.background = "#fee2e2";
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.color = "#94a3b8";
                        e.currentTarget.style.background = "none";
                    }}
                >
                    ✕
                </button>
            )
        }
    ], [handleDeleteStock]);

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;
        setLoading(true);
        const querySymbol = searchQuery.trim().toUpperCase();
        try {
            const response = await fetch(`api/fetchStockAnalysis?stock=${encodeURIComponent(querySymbol)}`);
            const stockData = await response.json();
            
            if (stockData) {
                const newEntry = {
                    stock: stockData.stock || querySymbol,
                    companyName: stockData.companyName || querySymbol,
                    currentPrice: stockData.currentPrice,
                    marketCap: stockData.marketCap,
                    peRatio: stockData.peRatio,
                    debtToEquity: stockData.debtToEquity,
                    rsi: stockData.rsi,
                    roce: stockData.roce,
                    roe: stockData.roe,
                    promoterHolding: stockData.promoterHolding,
                    promoterChange: stockData.promoterChange,
                    fiiHolding: stockData.fiiHolding,
                    fiiChange: stockData.fiiChange,
                    diiHolding: stockData.diiHolding,
                    diiChange: stockData.diiChange,
                    publicHolding: stockData.publicHolding,
                    quarterlyEps: stockData.quarterlyEps || [],
                    epsLast4Qtrs: stockData.epsLast4Qtrs || [],
                    // Historical PE median comparison
                    peMedian1Y: stockData.peMedian1Y ?? null,
                    peMedian3Y: stockData.peMedian3Y ?? null,
                    peMedian5Y: stockData.peMedian5Y ?? null,
                    belowMedian1Y: stockData.belowMedian1Y ?? null,
                    belowMedian3Y: stockData.belowMedian3Y ?? null,
                    belowMedian5Y: stockData.belowMedian5Y ?? null,
                };

                setAnalysisData(prev => {
                    const filtered = prev.filter(item => item.stock !== newEntry.stock);
                    return [newEntry, ...filtered];
                });
                setSelectedStock(newEntry);
            }
            setSearchQuery("");
        } catch (err) {
            console.error("Error fetching stock analysis:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleRowClick = (event) => {
        if (event?.data) {
            setSelectedStock(event.data);
        }
    };

    return (
        <AnalysisUI
            loading={loading}
            summary={summary}
            analysisData={analysisData}
            selectedStock={selectedStock}
            columnDefs={columnDefs}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            handleSearch={handleSearch}
            handleDeleteStock={handleDeleteStock}
            handleClearAll={handleClearAll}
            handleRowClick={handleRowClick}
            gridRef={gridRef}
        />
    );
};

export default Analysis;
