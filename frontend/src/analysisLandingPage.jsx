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
    
    const [activeTab, setActiveTab] = useState("fundamentals");
    const [selectedStrategy, setSelectedStrategy] = useState("sr_poc");
    
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

    const [cacheCleared, setCacheCleared] = useState(false);

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

    // Clear both frontend matrix and backend memory cache
    const handleClearCache = useCallback(async () => {
        try {
            await fetch("api/clearStockAnalysisCache", { method: "POST" });
        } catch (e) {
            console.error("Failed to clear backend cache:", e);
        }
        setAnalysisData([]);
        setSelectedStock(null);
        try {
            sessionStorage.removeItem(STORAGE_KEY);
        } catch (e) {}
        setCacheCleared(true);
        setTimeout(() => setCacheCleared(false), 2000);
    }, [STORAGE_KEY]);

    // Backward-compatible alias
    const handleClearAll = handleClearCache;

    // ── 1. Column Definitions for "Fundamentals & Health" Tab ─────────────
    const fundamentalColumnDefs = useMemo(() => [
        { 
            headerName: "Scrip", 
            field: "stock", 
            flex: 1.6,
            minWidth: 140,
            pinned: "left",
            cellRenderer: p => (
                <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", lineHeight: "1.3" }}>
                    <span style={{ fontWeight: "800", color: "#0f172a", fontSize: "15px" }}>{p.value}</span>
                    {p.data?.companyName && p.data.companyName !== p.value && (
                        <span style={{ fontSize: "12px", color: "#64748b", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                            {p.data.companyName}
                        </span>
                    )}
                </div>
            )
        },
        {
            headerName: "CMP (₹)",
            field: "currentPrice",
            flex: 1.1,
            minWidth: 105,
            valueFormatter: p => p.value ? `₹${Number(p.value).toLocaleString("en-IN")}` : "—",
            cellStyle: { fontWeight: "800", color: "#0f172a", fontSize: "15px" }
        },
        { 
            headerName: "Rating", 
            field: "ratingScore", 
            flex: 1.0,
            minWidth: 105,
            sortable: true,
            cellRenderer: p => {
                const score = p.value !== null && p.value !== undefined ? Number(p.value) : null;
                if (score === null) return <span style={{ color: "#94a3b8" }}>—</span>;
                
                let bg = "#f1f5f9";
                let textCol = "#475569";
                let borderCol = "#cbd5e1";
                if (score === 4) {
                    bg = "#dcfce7";
                    textCol = "#15803d";
                    borderCol = "#86efac";
                } else if (score === 3) {
                    bg = "#e0f2fe";
                    textCol = "#0369a1";
                    borderCol = "#7dd3fc";
                } else if (score === 2) {
                    bg = "#fef3c7";
                    textCol = "#b45309";
                    borderCol = "#fde68a";
                } else {
                    bg = "#fee2e2";
                    textCol = "#b91c1c";
                    borderCol = "#fca5a5";
                }

                const checks = p.data?.ratingChecks || {};
                const tooltipText = [
                    `Rating: ${score}/4 Checks Passed`,
                    `1. FII Peak Holding: ${checks.fiiHolding?.passed ? "✅ PASS" : "❌ FAIL"} (${checks.fiiHolding?.detail || "N/A"})`,
                    `2. P/E vs Medians: ${checks.peValuation?.passed ? "✅ PASS" : "❌ FAIL"} (${checks.peValuation?.detail || "N/A"})`,
                    `3. RSI ≤ 55: ${checks.rsiMomentum?.passed ? "✅ PASS" : "❌ FAIL"} (${checks.rsiMomentum?.detail || "N/A"})`,
                    `4. Consistent QoQ EPS: ${checks.epsGrowth?.passed ? "✅ PASS" : "❌ FAIL"} (${checks.epsGrowth?.detail || "N/A"})`
                ].join("\n");

                return (
                    <div title={tooltipText} style={{ display: "inline-flex", alignItems: "center", cursor: "help" }}>
                        <span style={{
                            background: bg,
                            color: textCol,
                            border: `1px solid ${borderCol}`,
                            padding: "4px 12px",
                            borderRadius: "14px",
                            fontWeight: "800",
                            fontSize: "13px",
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px"
                        }}>
                            {score === 4 && <span style={{ fontSize: "12px" }}>⭐</span>}
                            {score}/4
                        </span>
                    </div>
                );
            }
        },
        { 
            headerName: "P/E & Medians", 
            field: "peRatio", 
            flex: 1.9,
            minWidth: 190,
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
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "3px", lineHeight: "1.2", width: "100%" }}>
                        <span style={{ fontWeight: "800", fontSize: "15px", color: "#0f172a" }}>
                            {pe.toFixed(1)}x
                        </span>
                        <div style={{ display: "flex", gap: "4px", alignItems: "center", justifyContent: "center", flexWrap: "wrap" }}>
                            {m1y != null && (
                                <span title={`1Y Median PE: ${m1y}x`} style={{ 
                                    fontSize: "10px", fontWeight: "700", padding: "2px 5px", borderRadius: "4px",
                                    background: b1y ? "#dcfce7" : "#fee2e2",
                                    color: b1y ? "#15803d" : "#b91c1c"
                                }}>
                                    1Y {b1y ? "↓" : "↑"}{m1y}x
                                </span>
                            )}
                            {m3y != null && (
                                <span title={`3Y Median PE: ${m3y}x`} style={{ 
                                    fontSize: "10px", fontWeight: "700", padding: "2px 5px", borderRadius: "4px",
                                    background: b3y ? "#dcfce7" : "#fee2e2",
                                    color: b3y ? "#15803d" : "#b91c1c"
                                }}>
                                    3Y {b3y ? "↓" : "↑"}{m3y}x
                                </span>
                            )}
                            {m5y != null && (
                                <span title={`5Y Median PE: ${m5y}x`} style={{ 
                                    fontSize: "10px", fontWeight: "700", padding: "2px 5px", borderRadius: "4px",
                                    background: b5y ? "#dcfce7" : "#fee2e2",
                                    color: b5y ? "#15803d" : "#b91c1c"
                                }}>
                                    5Y {b5y ? "↓" : "↑"}{m5y}x
                                </span>
                            )}
                        </div>
                    </div>
                );
            }
        },
        { 
            headerName: "Debt / Eq", 
            field: "debtToEquity", 
            flex: 0.9,
            minWidth: 90,
            valueFormatter: p => (p.value !== null && p.value !== undefined) ? Number(p.value).toFixed(2) : "—",
            cellStyle: p => {
                const val = Number(p.value);
                const color = isNaN(val) ? "#64748b" : (val <= 0.5 ? "#10b981" : (val <= 1.2 ? "#f59e0b" : "#ef4444"));
                return { fontWeight: "700", color, textAlign: "center", fontSize: "14px" };
            }
        },
        { 
            headerName: "RSI (14)", 
            field: "rsi", 
            flex: 1.0,
            minWidth: 95,
            cellRenderer: p => {
                const val = Number(p.value);
                if (isNaN(val) || val === 0) return <span style={{ color: "#94a3b8" }}>—</span>;
                let bg = "#e0f2fe";
                let textCol = "#0369a1";
                if (val >= 70) {
                    bg = "#fee2e2";
                    textCol = "#b91c1c";
                } else if (val <= 30) {
                    bg = "#dcfce7";
                    textCol = "#15803d";
                }
                return (
                    <span style={{ 
                        background: bg, 
                        color: textCol, 
                        padding: "3px 10px", 
                        borderRadius: "14px", 
                        fontSize: "12px", 
                        fontWeight: "800" 
                    }}>
                        {val.toFixed(1)}
                    </span>
                );
            }
        },
        { 
            headerName: "EPS (4Q)", 
            field: "quarterlyEps", 
            flex: 1.8,
            minWidth: 180,
            cellRenderer: p => {
                const qEps = p.value || [];
                if (!qEps || qEps.length === 0) {
                    const last4 = p.data?.epsLast4Qtrs || [];
                    if (!last4 || last4.length === 0) return <span style={{ color: "#94a3b8" }}>—</span>;
                    return (
                        <div style={{ display: "flex", gap: "4px", alignItems: "center", justifyContent: "center", flexWrap: "wrap" }}>
                            {last4.map((val, idx) => (
                                <span key={idx} style={{ background: "#f1f5f9", padding: "2px 6px", borderRadius: "4px", fontSize: "11px", fontWeight: "700", color: "#334155" }}>
                                    ₹{Number(val).toFixed(1)}
                                </span>
                            ))}
                        </div>
                    );
                }
                return (
                    <div style={{ display: "flex", gap: "4px", alignItems: "center", justifyContent: "center", flexWrap: "wrap" }}>
                        {qEps.map((item, idx) => (
                            <span 
                                key={idx} 
                                title={`${item.quarter}: ₹${item.eps}`}
                                style={{ 
                                    background: "#f1f5f9", 
                                    color: "#1e293b", 
                                    padding: "2px 6px", 
                                    borderRadius: "4px", 
                                    fontSize: "11px", 
                                    fontWeight: "700",
                                    whiteSpace: "nowrap"
                                }}
                            >
                                <span style={{ color: "#64748b", fontSize: "9px", marginRight: "2px" }}>{item.quarter.slice(0, 3)}</span>
                                ₹{Number(item.eps).toFixed(1)}
                            </span>
                        ))}
                    </div>
                );
            }
        },
        { 
            headerName: "Promoter %", 
            field: "promoterHolding", 
            flex: 1.1,
            minWidth: 105,
            cellRenderer: p => {
                const val = p.value !== null && p.value !== undefined ? Number(p.value) : null;
                const change = p.data?.promoterChange !== null && p.data?.promoterChange !== undefined ? Number(p.data.promoterChange) : null;
                if (val === null) return <span style={{ color: "#94a3b8" }}>—</span>;
                return (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", lineHeight: "1.2" }}>
                        <span style={{ fontWeight: "700", color: "#1e293b", fontSize: "14px" }}>{val.toFixed(1)}%</span>
                        {change !== null && (
                            <span style={{ 
                                fontSize: "11px", 
                                fontWeight: "800", 
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
            headerName: "FII %", 
            field: "fiiHolding", 
            flex: 1.1,
            minWidth: 105,
            cellRenderer: p => {
                const val = p.value !== null && p.value !== undefined ? Number(p.value) : null;
                const change = p.data?.fiiChange !== null && p.data?.fiiChange !== undefined ? Number(p.data.fiiChange) : null;
                if (val === null) return <span style={{ color: "#94a3b8" }}>—</span>;
                return (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", lineHeight: "1.2" }}>
                        <span style={{ fontWeight: "700", color: "#1e293b", fontSize: "14px" }}>{val.toFixed(1)}%</span>
                        {change !== null && (
                            <span style={{ 
                                fontSize: "11px", 
                                fontWeight: "800", 
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
            headerName: "DII %", 
            field: "diiHolding", 
            flex: 1.1,
            minWidth: 105,
            cellRenderer: p => {
                const val = p.value !== null && p.value !== undefined ? Number(p.value) : null;
                const change = p.data?.diiChange !== null && p.data?.diiChange !== undefined ? Number(p.data.diiChange) : null;
                if (val === null) return <span style={{ color: "#94a3b8" }}>—</span>;
                return (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", lineHeight: "1.2" }}>
                        <span style={{ fontWeight: "700", color: "#1e293b", fontSize: "14px" }}>{val.toFixed(1)}%</span>
                        {change !== null && (
                            <span style={{ 
                                fontSize: "11px", 
                                fontWeight: "800", 
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
            minWidth: 60,
            sortable: false,
            filter: false,
            pinned: "right",
            cellRenderer: p => (
                <button
                    title={`Delete ${p.data?.stock} from matrix`}
                    onClick={(e) => {
                        e.stopPropagation();
                        if (p.data?.stock) handleDeleteStock(p.data.stock);
                    }}
                    style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        color: "#94a3b8",
                        fontSize: "16px",
                        padding: "6px 10px",
                        borderRadius: "6px",
                        transition: "color 0.15s, background 0.15s",
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = "#ef4444"; e.currentTarget.style.background = "#fee2e2"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = "#94a3b8"; e.currentTarget.style.background = "none"; }}
                >
                    ✕
                </button>
            )
        }
    ], [handleDeleteStock]);

    // ── 2. Column Definitions for "Trading Strategies" ────────────────────
    const strategyColumnDefs = useMemo(() => [
        { 
            headerName: "Scrip", 
            field: "stock", 
            flex: 1.4,
            minWidth: 100,
            pinned: "left",
            cellRenderer: p => (
                <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", lineHeight: "1.3" }}>
                    <span style={{ fontWeight: "800", color: "#0f172a", fontSize: "14px" }}>{p.value}</span>
                    {p.data?.companyName && p.data.companyName !== p.value && (
                        <span style={{ fontSize: "11px", color: "#64748b", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                            {p.data.companyName}
                        </span>
                    )}
                </div>
            )
        },
        { 
            headerName: "Signal", 
            field: "signalData", 
            flex: 1.1,
            minWidth: 95,
            sortable: true,
            cellRenderer: p => {
                const sigObj = p.data?.strategySignals?.[selectedStrategy] || p.value || {};
                const sig = sigObj.signal;
                if (!sig) return <span style={{ color: "#94a3b8" }}>—</span>;

                let bg = "#f1f5f9";
                let textCol = "#475569";
                let borderCol = "#cbd5e1";
                if (sig === "BUY") {
                    bg = "#dcfce7";
                    textCol = "#15803d";
                    borderCol = "#86efac";
                } else if (sig === "SELL") {
                    bg = "#fee2e2";
                    textCol = "#b91c1c";
                    borderCol = "#fca5a5";
                }

                return (
                    <span title={sigObj.reason || ""} style={{
                        background: bg,
                        color: textCol,
                        border: `1.5px solid ${borderCol}`,
                        padding: "4px 10px",
                        borderRadius: "12px",
                        fontWeight: "800",
                        fontSize: "12px",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "3px",
                        cursor: "help"
                    }}>
                        {sig === "BUY" ? "🟢 BUY" : (sig === "SELL" ? "🔴 SELL" : "⚪ HOLD")}
                    </span>
                );
            }
        },
        {
            headerName: "CMP (₹)",
            field: "currentPrice",
            flex: 0.9,
            minWidth: 80,
            valueFormatter: p => p.value ? `₹${Number(p.value).toLocaleString("en-IN")}` : "—",
            cellStyle: { fontWeight: "800", color: "#0f172a", fontSize: "14px" }
        },
        {
            headerName: "Target",
            field: "signalData",
            flex: 1.1,
            minWidth: 95,
            cellRenderer: p => {
                const sigObj = p.data?.strategySignals?.[selectedStrategy] || p.value || {};
                const target = sigObj.targetPrice;
                const cmp = p.data?.currentPrice;
                if (!target) return <span style={{ color: "#94a3b8" }}>—</span>;
                const upside = cmp ? ((target - cmp) / cmp * 100) : null;
                return (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", lineHeight: "1.2" }}>
                        <span style={{ fontWeight: "800", color: "#15803d", fontSize: "13px" }}>₹{target.toLocaleString("en-IN")}</span>
                        {upside !== null && (
                            <span style={{ fontSize: "10px", fontWeight: "800", color: "#16a34a" }}>+{upside.toFixed(1)}%</span>
                        )}
                    </div>
                );
            }
        },
        {
            headerName: "Stop Loss",
            field: "signalData",
            flex: 1.1,
            minWidth: 95,
            cellRenderer: p => {
                const sigObj = p.data?.strategySignals?.[selectedStrategy] || p.value || {};
                const sl = sigObj.stopLossPrice;
                const cmp = p.data?.currentPrice;
                if (!sl) return <span style={{ color: "#94a3b8" }}>—</span>;
                const downside = cmp ? ((sl - cmp) / cmp * 100) : null;
                return (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", lineHeight: "1.2" }}>
                        <span style={{ fontWeight: "800", color: "#b91c1c", fontSize: "13px" }}>₹{sl.toLocaleString("en-IN")}</span>
                        {downside !== null && (
                            <span style={{ fontSize: "10px", fontWeight: "800", color: "#dc2626" }}>{downside.toFixed(1)}%</span>
                        )}
                    </div>
                );
            }
        },
        {
            headerName: "R:R Ratio",
            field: "signalData",
            flex: 0.8,
            minWidth: 70,
            cellRenderer: p => {
                const sigObj = p.data?.strategySignals?.[selectedStrategy] || p.value || {};
                const rr = sigObj.riskRewardRatio;
                if (!rr) return <span style={{ color: "#94a3b8" }}>—</span>;
                return (
                    <span style={{ fontWeight: "800", color: rr >= 2 ? "#15803d" : "#0f172a", fontSize: "13px" }}>
                        1:{rr}
                    </span>
                );
            }
        },
        {
            headerName: "S1 (Support)",
            field: "supports",
            flex: 1.1,
            minWidth: 95,
            sortable: false,
            cellRenderer: p => {
                const supports = p.value || [];
                if (!supports.length) return <span style={{ color: "#94a3b8" }}>—</span>;
                const s1 = supports[0];
                const dist = p.data?.distanceToSupport1Pct;
                const stars = "★".repeat(Math.min(s1.strength, 4));
                return (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", lineHeight: "1.2" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "3px" }}>
                            <span style={{ fontWeight: "700", color: "#15803d", fontSize: "12px" }}>₹{s1.price.toLocaleString("en-IN")}</span>
                            <span style={{ fontSize: "9px", color: "#f59e0b" }}>{stars}</span>
                        </div>
                        {dist !== null && (
                            <span style={{ fontSize: "10px", fontWeight: "800", color: "#15803d" }}>{dist.toFixed(1)}%</span>
                        )}
                    </div>
                );
            }
        },
        {
            headerName: "R1 (Resistance)",
            field: "resistances",
            flex: 1.1,
            minWidth: 95,
            sortable: false,
            cellRenderer: p => {
                const resistances = p.value || [];
                if (!resistances.length) return <span style={{ color: "#94a3b8" }}>—</span>;
                const r1 = resistances[0];
                const dist = p.data?.distanceToResistance1Pct;
                const stars = "★".repeat(Math.min(r1.strength, 4));
                return (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", lineHeight: "1.2" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "3px" }}>
                            <span style={{ fontWeight: "700", color: "#dc2626", fontSize: "12px" }}>₹{r1.price.toLocaleString("en-IN")}</span>
                            <span style={{ fontSize: "9px", color: "#f59e0b" }}>{stars}</span>
                        </div>
                        {dist !== null && (
                            <span style={{ fontSize: "10px", fontWeight: "800", color: "#b91c1c" }}>+{dist.toFixed(1)}%</span>
                        )}
                    </div>
                );
            }
        },
        {
            headerName: "Volume POC",
            field: "poc",
            flex: 1.1,
            minWidth: 95,
            sortable: false,
            cellRenderer: p => {
                const poc = p.value;
                if (!poc) return <span style={{ color: "#94a3b8" }}>—</span>;
                const cmp = p.data?.currentPrice;
                const dist = cmp ? ((poc.price - cmp) / cmp * 100) : null;
                return (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", lineHeight: "1.2" }}>
                        <span style={{ fontWeight: "800", color: "#92400e", fontSize: "12px" }}>🎯 ₹{poc.price.toLocaleString("en-IN")}</span>
                        {dist !== null && (
                            <span style={{ fontSize: "10px", fontWeight: "700", color: "#78716c" }}>{dist.toFixed(1)}%</span>
                        )}
                    </div>
                );
            }
        },
        { 
            headerName: "RSI", 
            field: "rsi", 
            flex: 0.7,
            minWidth: 60,
            cellRenderer: p => {
                const val = Number(p.value);
                if (isNaN(val) || val === 0) return <span style={{ color: "#94a3b8" }}>—</span>;
                let bg = "#e0f2fe";
                let textCol = "#0369a1";
                if (val >= 70) { bg = "#fee2e2"; textCol = "#b91c1c"; }
                else if (val <= 30) { bg = "#dcfce7"; textCol = "#15803d"; }
                return (
                    <span style={{ background: bg, color: textCol, padding: "2px 7px", borderRadius: "12px", fontSize: "11px", fontWeight: "800" }}>
                        {val.toFixed(1)}
                    </span>
                );
            }
        },
        {
            headerName: "Action",
            field: "action",
            flex: 0.5,
            minWidth: 45,
            sortable: false,
            filter: false,
            pinned: "right",
            cellRenderer: p => (
                <button
                    title={`Delete ${p.data?.stock} from matrix`}
                    onClick={(e) => {
                        e.stopPropagation();
                        if (p.data?.stock) handleDeleteStock(p.data.stock);
                    }}
                    style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        color: "#94a3b8",
                        fontSize: "15px",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        transition: "color 0.15s, background 0.15s",
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = "#ef4444"; e.currentTarget.style.background = "#fee2e2"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = "#94a3b8"; e.currentTarget.style.background = "none"; }}
                >
                    ✕
                </button>
            )
        }
    ], [handleDeleteStock, selectedStrategy]);

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;
        setLoading(true);
        
        // Extract unique uppercase tokens split by commas, spaces, newlines, semicolons, tabs
        const rawTokens = searchQuery.split(/[\s,;\n\t]+/).map(s => s.trim().toUpperCase()).filter(Boolean);
        const uniqueSymbols = Array.from(new Set(rawTokens));
        if (uniqueSymbols.length === 0) {
            setLoading(false);
            return;
        }

        try {
            const queryParam = uniqueSymbols.join(",");
            const response = await fetch(`api/fetchStockAnalysis?stock=${encodeURIComponent(queryParam)}`);
            const data = await response.json();
            
            const resultsArray = Array.isArray(data) ? data : (data && data.stock ? [data] : []);
            
            if (resultsArray.length > 0) {
                const newEntries = resultsArray.map(stockData => ({
                    stock: stockData.stock,
                    companyName: stockData.companyName || stockData.stock,
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
                    // 4-Check Rating
                    ratingScore: stockData.ratingScore ?? null,
                    maxScore: stockData.maxScore ?? 4,
                    ratingChecks: stockData.ratingChecks || {},
                    fiiHistory: stockData.fiiHistory || [],
                    // Support & Resistance + Volume Profile POC
                    supports: stockData.supports || [],
                    resistances: stockData.resistances || [],
                    distanceToSupport1Pct: stockData.distanceToSupport1Pct ?? null,
                    distanceToResistance1Pct: stockData.distanceToResistance1Pct ?? null,
                    poc: stockData.poc || null,
                    // Live Signals & Multi-Strategy Dictionary
                    signalData: stockData.signalData || {},
                    strategySignals: stockData.strategySignals || {},
                }));

                setAnalysisData(prev => {
                    const newKeys = new Set(newEntries.map(e => e.stock));
                    const filteredPrev = prev.filter(item => !newKeys.has(item.stock));
                    return [...newEntries, ...filteredPrev];
                });

                if (newEntries.length > 0) {
                    setSelectedStock(newEntries[0]);
                }
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
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            selectedStrategy={selectedStrategy}
            setSelectedStrategy={setSelectedStrategy}
            columnDefs={activeTab === "strategies" ? strategyColumnDefs : fundamentalColumnDefs}
            fundamentalColumnDefs={fundamentalColumnDefs}
            strategyColumnDefs={strategyColumnDefs}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            handleSearch={handleSearch}
            handleDeleteStock={handleDeleteStock}
            handleClearAll={handleClearAll}
            handleClearCache={handleClearCache}
            cacheCleared={cacheCleared}
            handleRowClick={handleRowClick}
            gridRef={gridRef}
        />
    );
};

export default Analysis;
