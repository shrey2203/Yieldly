import { useState, useEffect } from "react";
import { AgGridReact } from "ag-grid-react";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

const DEFAULT_STRATEGIES = [
    {
        id: "sr_poc",
        title: "S/R & Robust Volume Profile POC Floor",
        category: "Institutional Mean Reversion",
        badge: "🎯 S/R & POC",
        shortDescription: "Buys near institutional support zones and Robust Volume POC with low RSI, exiting at resistance ceilings.",
        writeup: {
            philosophy: (
                "Heavy volume accumulations (Point of Control) and historical swing reaction lows represent price levels where large institutions defend positions. " +
                "Entering near these validated floors provides a tight, well-defined stop loss with large upside to the next overhead resistance zone."
            ),
            buyRules: [
                "Support Confluence: Price is within -3.5% to +1.0% of Key Support (S1) or Robust Volume POC floor.",
                "RSI Cool-off: 14-day RSI ≤ 58.0 (guaranteeing room for momentum expansion before reaching overbought).",
                "Candle Confirmation: Daily close finishes in upper half of range, rejecting lower price levels."
            ],
            sellRules: [
                "Resistance Target: Price tests overhead Resistance ceiling (R1 ± 1.5%) or hits +12.0% take-profit.",
                "Overbought Warning: 14-day RSI ≥ 68.0 indicating exhaustion of short-term buying power."
            ],
            stopLossRules: [
                "Floor Breach: Strict hard stop placed at S1 Support × 0.965 (3.5% below the support level).",
                "Trend Breakdown: Exit if daily close violates 50-day SMA by > 5%."
            ],
            idealMarket: "Range-bound markets, institutional consolidation channels, and high-quality value/growth compounders."
        }
    },
    {
        id: "ema_momentum",
        title: "20/50 EMA Trend & Volume Surge",
        category: "Momentum & Trend Following",
        badge: "⚡ Momentum",
        shortDescription: "Rides institutional momentum by buying 20 EMA pullbacks in 200 EMA bull regimes with volume expansion.",
        writeup: {
            philosophy: (
                "Institutional accumulation creates sustained momentum where the 20-day Exponential Moving Average acts as a dynamic launchpad. " +
                "Rather than chasing extended tops, this strategy waits for shallow consolidations or fresh golden crossovers to enter with an asymmetric risk-reward ratio."
            ),
            buyRules: [
                "Macro Bull Regime: Daily Close must be strictly above the 200 EMA (Bull market baseline).",
                "Intermediate Uptrend: 20 EMA must be trading above the 50 EMA.",
                "Pullback / Breakout Trigger: Price pulls back to test the 20 EMA (within 2.0%) or 20 EMA crosses above 50 EMA within the last 3 days.",
                "Volume Confirmation: Daily Volume must exceed 1.3× of the 20-day Volume SMA (Institutional participation).",
                "RSI Sweet Spot: 14-period RSI must be between 45.0 and 65.0 (bullish expansion zone, avoiding overbought traps)."
            ],
            sellRules: [
                "Profit Target: Dynamic Take-Profit set at Entry + 2.5× ATR(14) (yielding approx. +10% to +16% gain).",
                "Momentum Exhaustion: Daily RSI closes above 75.0 (Overbought blow-off top warning).",
                "Trend Breakdown: Daily close breaks below the 50-day EMA."
            ],
            stopLossRules: [
                "Initial Stop Loss: Set at 50 EMA × 0.98 or Entry - 1.8× ATR(14) (strictly capped at 4.5% max risk).",
                "Breakeven Trailing: Once the trade reaches +6.0% profit, the Stop Loss is automatically trailed to Breakeven (Entry Price).",
                "Profit Protection: Once trade reaches +10.0%, trailing SL locks in at least +5.0% profit."
            ],
            idealMarket: "Strong trending bull markets, high-growth midcaps, and institutional momentum leaders."
        }
    },
    {
        id: "supertrend_breakout",
        title: "Supertrend (10, 3) Volatility Breakout",
        category: "Trend Following & Volatility",
        badge: "🚀 Supertrend",
        shortDescription: "Captures multi-month momentum moves by entering on Supertrend bull flips with dynamic ATR trailing stops.",
        writeup: {
            philosophy: (
                "The Supertrend indicator combines Average True Range (ATR) with median price bands to adapt dynamically to market volatility. " +
                "By entering when price breaks above the upper volatility band and trailing stops along the lower band, it allows winning trades to run indefinitely " +
                "while instantly cutting losses when market structure fails."
            ),
            buyRules: [
                "Supertrend Bull Flip: Supertrend indicator flips from Red (Bearish) to Green (Bullish) as daily Close crosses above the upper ATR band.",
                "Trend Validation: Daily Close is higher than 50 EMA.",
                "Volume Confirmation: Breakout candle volume is at least 1.15× of 20-day Volume SMA.",
                "RSI Momentum: RSI(14) > 48.0 (confirming active buying interest)."
            ],
            sellRules: [
                "Supertrend Bear Flip: Supertrend flips from Green (Bullish) to Red (Bearish) as price breaches the trailing support line.",
                "Overbought Exhaustion: RSI closes above 78.0 with a topping wick candle.",
                "Target Extension: Discretionary take-profit at +18.0% gain from entry."
            ],
            stopLossRules: [
                "Dynamic Trailing Stop: Strictly anchored to the live Supertrend Green line value.",
                "Max Hard Stop: 5.0% maximum risk from entry price if volatility spikes.",
                "Profit Lock: As the Supertrend line ratchets upward, all paper profits are progressively locked in."
            ],
            idealMarket: "Strong cyclical rallies, breakout expansions, and trending sector rotations."
        }
    },
    {
        id: "dual_momentum_200sma",
        title: "200-Day Trend & Dual Momentum (Honest Quant)",
        category: "Academic Trend Following & Dual Momentum",
        badge: "🏛️ 200D Momentum",
        shortDescription: "Academic honest rule: buys assets in verified 200-day SMA bull regimes with 12M/3M positive momentum and ATR risk management.",
        writeup: {
            philosophy: (
                "Based on Meb Faber's landmark 200-day quantitative trend timing and Gary Antonacci's Dual Momentum framework. " +
                "By requiring positive absolute momentum (Price strictly above the 200-day SMA) combined with positive intermediate " +
                "relative momentum (12-month and 3-month return expansion), this strategy completely sidesteps catastrophic bear-market drawdowns " +
                "without snooping or over-optimizing parameters."
            ),
            buyRules: [
                "Macro Trend Baseline: Daily Close must be strictly above the 200-day Simple Moving Average (Price > 200 SMA).",
                "Intermediate Momentum: 12-month (252-day) return > 0% AND 3-month (63-day) return > 3.0%.",
                "Uptrend Structure: 20-day SMA is trading above the 50-day SMA.",
                "Controlled Pullback: Price is within -2.0% to +3.0% of the 20-day SMA (entering on support rather than chasing extended tops).",
                "RSI Momentum Window: 14-period RSI is between 42.0 and 65.0 (healthy bullish expansion zone)."
            ],
            sellRules: [
                "Macro Regime Collapse: Daily close breaks below the 200-day SMA (immediate risk-off exit to cash).",
                "Overbought Blow-off: 14-day RSI closes above 76.0 with price extended > 18% above the 200-day SMA.",
                "Profit Target: Reaches dynamic take-profit at Entry + 2.5× ATR(14) (yielding approx. +12% to +18% gain).",
                "Intermediate Breakdown: Daily close breaks below the 50-day SMA by > 2.0%."
            ],
            stopLossRules: [
                "Initial Risk Stop: Placed at max(50 SMA × 0.975, Entry - 2.0× ATR) — strictly capped at 5.0% maximum risk.",
                "Breakeven Ratchet: Once trade gains +6.5%, the Stop Loss is automatically ratcheted to Breakeven.",
                "Trailing Floor: Once trade reaches +11.0%, Stop Loss trails below the 50-day SMA to protect accrued gains."
            ],
            idealMarket: "Broad multi-year secular bull markets, structural sector leaders, and liquid index compounders."
        }
    },
    {
        id: "zscore_mean_reversion",
        title: "Z-Score (20D) Statistical Mean Reversion",
        category: "Statistical Arbitrage & Mean Reversion",
        badge: "📐 Z-Score Reversion",
        shortDescription: "Exploits statistical outliers (Z <= -2.0, 95% confidence interval) to capture rapid mean reversion back to equilibrium.",
        writeup: {
            philosophy: (
                "According to the central limit theorem and statistical distribution of asset returns, price extensions beyond " +
                "2.0 standard deviations from the 20-day rolling mean occur less than 5% of the time in normal markets. " +
                "When an asset reaches Z <= -2.0 with oversold RSI and stabilizing price action, institutional liquidity steps in " +
                "to push the asset back toward equilibrium (Z = 0)."
            ),
            buyRules: [
                "Statistical Oversold Outlier: 20-day Rolling Z-Score is at or below -2.0 (Price is > 2.0 standard deviations below 20-day SMA).",
                "RSI Exhaustion: 14-day RSI <= 38.0 or recovering upward from oversold territory.",
                "Price Stabilization: Today's Close finishes above yesterday's Low (rejection of extreme downside expansion)."
            ],
            sellRules: [
                "Equilibrium Target: Price reverts to the 20-day SMA (Z = 0.0) or tests upper statistical band (Z >= +1.5).",
                "Overbought Outlier: 20-day Z-Score reaches >= +2.0 (statistically overextended to the upside).",
                "RSI Exhaustion: 14-day RSI crosses above 70.0."
            ],
            stopLossRules: [
                "Extreme Tail Risk Stop: Placed at Entry - 2.2× ATR(14) (or Z <= -3.2 fat-tail breakdown).",
                "Breakeven Floor: Once the trade reverts +5.0% toward the mean, Stop Loss moves to Breakeven.",
                "Time Stop: If mean reversion does not occur within 20 trading days, exit position to free up capital."
            ],
            idealMarket: "Mean-reverting range-bound stocks, large-cap liquid equities, and stable dividend compounders."
        }
    },
    {
        id: "volatility_targeting",
        title: "Volatility-Targeted (ATR) Breakout",
        category: "Volatility Management & Breakout",
        badge: "🌊 Vol Breakout",
        shortDescription: "Enters breakouts during quiet volatility compressions and sizes risk dynamically via 20D vs 100D realized volatility.",
        writeup: {
            philosophy: (
                "Volatility clusters and mean-reverts. Breakouts that occur after periods of volatility compression (low realized vol) " +
                "have the highest probability of initiating multi-month sustained trends. By dynamically targeting a stable annualized volatility " +
                "and using ATR trailing channels, capital is protected from erratic late-stage mania."
            ),
            buyRules: [
                "20-Day Donchian Breakout: Daily Close crosses above the 20-day High.",
                "Volatility Compression Gate: 20-day Realized Volatility <= 1.25× 100-day Baseline Volatility (not buying into wild chaos).",
                "Trend Regime: Price is trading above the 50-day and 200-day SMAs.",
                "RSI Momentum: 14-day RSI is between 50.0 and 68.0."
            ],
            sellRules: [
                "Channel Violation: Daily close breaks below the 10-day Donchian Low.",
                "Volatility Blow-off Spike: Realized Volatility spikes > 2.5× baseline (erratic climax top warning).",
                "Profit Target: Dynamic expansion target hit at Entry + 3.0× ATR(14)."
            ],
            stopLossRules: [
                "Initial ATR Floor: Hard stop placed at max(20-day Low, Entry - 2.0× ATR(14)) — strictly capped at 5.0%.",
                "Volatility Ratchet: Once price gains +7.0%, Stop Loss ratchets to Breakeven.",
                "Trailing 10-Day Channel: Once price gains +12.0%, Stop Loss trails tightly along the 10-day Low."
            ],
            idealMarket: "Emerging growth breakouts, sector rotation momentum, and post-consolidation rally phases."
        }
    },
    {
        id: "cross_sectional_momentum",
        title: "12-1M Quantitative Relative Momentum",
        category: "Academic Momentum Anomaly",
        badge: "🚀 12M Momentum",
        shortDescription: "Classic academic 12-1 Month momentum (Jegadeesh & Titman) filtering out short-term 1M microstructure reversal.",
        writeup: {
            philosophy: (
                "Documented by Narasimhan Jegadeesh and Sheridan Titman (Journal of Finance, 1993), assets with superior past 12-month returns " +
                "continue to outperform over intermediate 3-12 month horizons due to slow institutional information diffusion and earnings drift. " +
                "Skipping the most recent month (21 days) completely removes short-term bid-ask microstructure noise and reversal traps."
            ),
            buyRules: [
                "12-1M Momentum Anomaly: Return over the past 252 days skipping the last 21 days (t-252 to t-21) exceeds +15.0%.",
                "Intermediate 6-Month Trend: Return over the past 126 days is strictly positive (> +6.0%).",
                "Regime Confirmation: Price is trading above both the 50-day and 200-day Simple Moving Averages.",
                "Healthy Momentum RSI: 14-day RSI is between 46.0 and 68.0 (active momentum expansion without topping)."
            ],
            sellRules: [
                "Intermediate Breakdown: Daily close breaks below the 50-day SMA by > 2.5%.",
                "6-Month Momentum Negative: Intermediate 6-month return turns negative (loss of leadership status).",
                "Overbought Blow-off: RSI crosses above 78.0 with extreme extension > 25% above 200 SMA.",
                "Profit Target: Dynamic milestone target reached at +20.0% gain from entry."
            ],
            stopLossRules: [
                "Initial Stop Loss: Placed at max(50 SMA × 0.97, Entry - 2.2× ATR(14)) — strictly capped at 5.0% risk.",
                "Breakeven Floor: Once trade gains +7.0%, Stop Loss automatically ratchets to Breakeven.",
                "Trailing Moving Average: Once trade exceeds +12.0%, Stop Loss trails tightly below the rising 50-day SMA."
            ],
            idealMarket: "Sustained secular bull trends, high relative-strength market leaders, and earnings compounders."
        }
    },
    {
        id: "coffee_can_compounder",
        title: "Coffee Can Quality Compounder (Multi-Year)",
        category: "Long-Term Quality & Compounding",
        badge: "☕ Coffee Can",
        shortDescription: "Long-term wealth compounding strategy buying market leaders in verified 200D secular bull trends with wide trailing stops.",
        writeup: {
            philosophy: (
                "Based on Robert Kirby's original 1984 concept and Saurabh Mukherjea's Coffee Can Investing framework. " +
                "True long-term wealth is generated not by hyperactive trading, but by identifying high-quality structural compounders, " +
                "buying them during consolidations, and holding them for multiple years to let business earnings growth drive returns. " +
                "Short-term volatility is treated as noise, with exits triggered strictly on structural macro breakdown."
            ),
            buyRules: [
                "Secular Bull Regime: Price is trading strictly above the rising 200-day SMA (Golden Cross: 50 SMA > 200 SMA).",
                "Healthy Consolidation Entry: Price is within -4.0% to +6.0% of the 50-day SMA (buying on value/support rather than chasing).",
                "Earnings Compounder: Long-term multi-quarter earnings stability and low financial leverage.",
                "Accumulation RSI: 14-day RSI is between 40.0 and 64.0 (institutional accumulation phase)."
            ],
            sellRules: [
                "Secular Trend Breakdown: Daily close breaks below the 200-day SMA by > 5.0% (structural bear market regime switch).",
                "Fundamental Earnings Collapse: Multiple consecutive quarters of severe EPS contraction.",
                "Parabolic Re-rating: Price extends > 45% above the 200-day SMA with RSI > 80 (take-profit on extreme euphoria)."
            ],
            stopLossRules: [
                "Wide Long-Term Stop: Placed safely below the 200-day SMA (200 SMA × 0.92) to prevent getting whipsawed by normal cyclical corrections.",
                "Compounding Trailing Floor: Once the position gains +20.0%, Stop Loss trails below the rising 200-day SMA, locking in long-term capital gains."
            ],
            idealMarket: "Multi-year secular economic expansions, monopoly/duopoly moat franchises, and structural compounders."
        }
    },
    {
        id: "canslim_growth",
        title: "CANSLIM Institutional Growth & Leadership",
        category: "Long-Term Growth & Leadership",
        badge: "🏆 CANSLIM Growth",
        shortDescription: "William O'Neil's classic methodology: buys market leaders breaking out of consolidation bases with earnings acceleration.",
        writeup: {
            philosophy: (
                "William O'Neil's CANSLIM system is the most successful growth stock methodology in investing history. " +
                "It combines accelerating quarterly earnings and institutional sponsorship (FII/DII accumulation) with " +
                "technical breakouts to 52-week highs. Rather than buying cheap laggards, CANSLIM invests exclusively " +
                "in the top 2% of market leaders."
            ),
            buyRules: [
                "Market Leadership & Uptrend: Price is strictly above the 50-day and 200-day SMAs (50 SMA > 200 SMA).",
                "Base Breakout: Price is trading within 5.0% of its 52-week (252-day) High.",
                "Volume Accumulation: 5-day average volume exceeds 20-day average volume (institutional pocket pivot).",
                "Momentum Sweet Spot: 14-day RSI is between 52.0 and 70.0 (strong active leadership expansion)."
            ],
            sellRules: [
                "Loss of 50-Day Moving Average: Daily close breaks below the 50-day SMA by > 3.0% on expanding volume.",
                "Climax Top Exhaustion: RSI reaches > 80.0 with price extended > 35% above the 50-day SMA.",
                "Major Compounding Milestone: Reaches profit target of +35% to +50% from base breakout."
            ],
            stopLossRules: [
                "Strict 7%-8% Hard Stop: Hard cut placed at Entry × 0.925 (O'Neil's golden rule of never taking more than an 8% loss).",
                "Trailing 50-Day Floor: Once the stock gains +15.0%, Stop Loss automatically trails below the rising 50-day SMA."
            ],
            idealMarket: "New market bull uptrends, tech & manufacturing sector leaders, and high ROE growth midcaps."
        }
    },
    {
        id: "deep_value_pe",
        title: "Deep Value & P/E Historical Discount",
        category: "Long-Term Value & Fundamental Re-rating",
        badge: "💎 Deep Value",
        shortDescription: "Buys profitable companies trading at deep discounts below 3Y/5Y median P/E and holds for long-term valuation re-rating.",
        writeup: {
            philosophy: (
                "Based on classic Benjamin Graham and Warren Buffett Value Principles. " +
                "Market sentiment oscillates between unwarranted euphoria and excessive pessimism. When high-quality, profitable " +
                "businesses trade at a 15% to 35% discount below their 3-year and 5-year historical median valuations, patient long-term " +
                "investors capture dual gains: underlying business earnings growth PLUS multiple expansion (P/E re-rating back to historical norms)."
            ),
            buyRules: [
                "Valuation Discount: Current P/E is strictly below the 3-Year and 5-Year Median P/E by at least 10.0%.",
                "Balance Sheet Strength: Low debt leverage with sustained operational profitability.",
                "Oversold Value Floor: 14-day RSI is between 32.0 and 55.0 (accumulating on extreme market apathy/neglect).",
                "Base Consolidation: Price is stabilizing within 5.0% of key long-term structural support."
            ],
            sellRules: [
                "Fair Value Re-rating: P/E expands to touch or exceed 1.15× of the 5-Year Historical Median P/E.",
                "Valuation Euphoria: 14-day RSI crosses above 78.0 with price extended > 30% above the 200-day SMA.",
                "Structural Business Decay: Severe continuous earnings contraction or structural debt escalation."
            ],
            stopLossRules: [
                "Structural Floor Cut: Hard stop placed at Entry × 0.88 (giving value mean-reversion 12% margin of safety to absorb market noise).",
                "Compounding Trailing Stop: Once the position gains +25.0%, Stop Loss trails below the 200-day SMA to protect re-rated profits."
            ],
            idealMarket: "Market corrections, unloved cyclical troughs, cash-generative value leaders, and high dividend yield compounders."
        }
    }
];

const AnalysisUI = ({ 
    loading, 
    summary, 
    analysisData = [], 
    selectedStock, 
    activeTab = "fundamentals",
    setActiveTab,
    selectedStrategy = "sr_poc",
    setSelectedStrategy,
    columnDefs, 
    searchQuery, 
    setSearchQuery, 
    handleSearch, 
    handleClearAll,
    handleClearCache,
    cacheCleared,
    handleRowClick, 
    gridRef 
}) => {
    const onClearClick = handleClearCache || handleClearAll;
    
    // Strategies state
    const [strategiesList, setStrategiesList] = useState(DEFAULT_STRATEGIES);
    const [showStrategyWriteup, setShowStrategyWriteup] = useState(true);

    // Backtest data state
    const [backtestData, setBacktestData] = useState(null);
    const [backtestLoading, setBacktestLoading] = useState(false);
    const [showTradeLog, setShowTradeLog] = useState(false);

    // Fetch strategies metadata from backend
    useEffect(() => {
        fetch("api/fetchAvailableStrategies")
            .then(res => res.json())
            .then(data => {
                if (Array.isArray(data) && data.length > 0) {
                    setStrategiesList(data);
                }
            })
            .catch(err => {
                console.warn("Using default strategy definitions:", err);
            });
    }, []);

    // Current active strategy info
    const activeStrategyInfo = strategiesList.find(s => s.id === selectedStrategy) || strategiesList[0];

    // Current active signal for selected stock
    const currentStockSignal = selectedStock?.strategySignals?.[selectedStrategy] || selectedStock?.signalData || {};

    // Dynamic strategy counts
    const buyCount = (analysisData || []).filter(d => {
        const sig = d.strategySignals?.[selectedStrategy]?.signal || d.signalData?.signal;
        return sig === "BUY";
    }).length;

    // Fetch backtest simulation when stock OR strategy changes
    useEffect(() => {
        if (!selectedStock?.stock) {
            setBacktestData(null);
            return;
        }

        let isMounted = true;
        setBacktestLoading(true);

        const stratParam = selectedStrategy || "sr_poc";
        fetch(`api/backtestStockStrategy?stock=${encodeURIComponent(selectedStock.stock)}&strategy=${encodeURIComponent(stratParam)}&years=2`)
            .then(res => res.json())
            .then(data => {
                if (isMounted) {
                    if (data?.status === "success") {
                        setBacktestData(data);
                    } else {
                        setBacktestData(null);
                    }
                    setBacktestLoading(false);
                }
            })
            .catch(err => {
                if (isMounted) {
                    console.error("Error fetching backtest data:", err);
                    setBacktestData(null);
                    setBacktestLoading(false);
                }
            });

        return () => {
            isMounted = false;
        };
    }, [selectedStock?.stock, selectedStrategy]);

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
                        Stock Fundamental & Strategy Hub
                    </h1>
                    <p style={{ margin: "4px 0 0 0", color: "#64748b", fontSize: "13px" }}>
                        Inspect P/E valuation, EPS growth, institutional patterns, or simulate quantitative trading strategies
                    </p>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
                    <div className="date-filters" style={{ display: "flex", alignItems: "center", gap: "10px", background: "white", padding: "6px 12px", borderRadius: "8px", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
                        <input 
                            type="text" 
                            placeholder="Enter scrips (e.g. ABB, SANGHVIMOV, TECHM)..." 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                            style={{ 
                                padding: "8px 12px", 
                                borderRadius: "6px", 
                                border: "1px solid #cbd5e1",
                                fontSize: "13px",
                                outline: "none",
                                width: "300px"
                            }}
                        />
                        <button 
                            onClick={handleSearch}
                            disabled={loading}
                            style={{
                                background: loading ? "#94a3b8" : "#0284c7",
                                color: "white",
                                border: "none",
                                padding: "8px 16px",
                                borderRadius: "6px",
                                fontWeight: "600",
                                cursor: loading ? "not-allowed" : "pointer",
                                fontSize: "13px",
                                display: "flex",
                                alignItems: "center",
                                gap: "6px"
                            }}
                        >
                            {loading ? "Analyzing..." : "Analyze"}
                        </button>
                    </div>

                    <button
                        onClick={onClearClick}
                        disabled={cacheCleared}
                        title="Clear browser cache and backend memory cache to refetch live data"
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "6px",
                            padding: "8px 14px",
                            borderRadius: "8px",
                            border: `1px solid ${cacheCleared ? "#86efac" : "#e2e8f0"}`,
                            background: cacheCleared ? "#f0fdf4" : "#f8fafc",
                            color: cacheCleared ? "#15803d" : "#64748b",
                            fontSize: "12px",
                            fontWeight: "600",
                            cursor: cacheCleared ? "default" : "pointer",
                            boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
                            transition: "all 0.2s ease"
                        }}
                    >
                        <span>{cacheCleared ? "✓" : "🗑️"}</span>
                        <span>{cacheCleared ? "Cache Cleared!" : "Clear Cache"}</span>
                    </button>
                </div>
            </header>

            {/* 2. Top-Level Tab Switcher */}
            <div style={{ display: "flex", gap: "8px", borderBottom: "2px solid #e2e8f0", marginBottom: "20px" }}>
                <button
                    onClick={() => setActiveTab && setActiveTab("fundamentals")}
                    style={{
                        display: "flex", alignItems: "center", gap: "8px",
                        padding: "10px 20px", borderRadius: "8px 8px 0 0",
                        fontSize: "14px", fontWeight: "700", cursor: "pointer",
                        border: "none",
                        background: activeTab === "fundamentals" ? "#0284c7" : "transparent",
                        color: activeTab === "fundamentals" ? "white" : "#64748b",
                        boxShadow: activeTab === "fundamentals" ? "0 -2px 6px rgba(2,132,199,0.2)" : "none",
                        transition: "all 0.2s ease"
                    }}
                >
                    <span>📊</span>
                    <span>Fundamentals & Health</span>
                    <span style={{
                        background: activeTab === "fundamentals" ? "rgba(255,255,255,0.25)" : "#e2e8f0",
                        color: activeTab === "fundamentals" ? "white" : "#475569",
                        padding: "2px 8px", borderRadius: "10px", fontSize: "11px", fontWeight: "800"
                    }}>
                        {analysisData?.length || 0}
                    </span>
                </button>

                <button
                    onClick={() => setActiveTab && setActiveTab("strategies")}
                    style={{
                        display: "flex", alignItems: "center", gap: "8px",
                        padding: "10px 20px", borderRadius: "8px 8px 0 0",
                        fontSize: "14px", fontWeight: "700", cursor: "pointer",
                        border: "none",
                        background: activeTab === "strategies" ? "#0284c7" : "transparent",
                        color: activeTab === "strategies" ? "white" : "#64748b",
                        boxShadow: activeTab === "strategies" ? "0 -2px 6px rgba(2,132,199,0.2)" : "none",
                        transition: "all 0.2s ease"
                    }}
                >
                    <span>🎯</span>
                    <span>Quant Strategy & Backtests</span>
                    {buyCount > 0 && (
                        <span style={{
                            background: activeTab === "strategies" ? "#16a34a" : "#dcfce7",
                            color: activeTab === "strategies" ? "white" : "#15803d",
                            padding: "2px 8px", borderRadius: "10px", fontSize: "11px", fontWeight: "800"
                        }}>
                            {buyCount} BUY
                        </span>
                    )}
                </button>
            </div>

            {/* 3. Strategy Selector & Write-up (Rendered ONLY in Quant Strategy Tab) */}
            {activeTab === "strategies" && (
                <div style={{ background: "white", borderRadius: "12px", padding: "16px 20px", marginBottom: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)", border: "1.5px solid #e0f2fe" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "14px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                            <span style={{ fontSize: "24px" }}>⚡</span>
                            <div>
                                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                    <label style={{ fontSize: "14px", fontWeight: "800", color: "#0f172a" }}>
                                        Active Strategy Model:
                                    </label>
                                    <select
                                        value={selectedStrategy}
                                        onChange={(e) => setSelectedStrategy && setSelectedStrategy(e.target.value)}
                                        style={{
                                            padding: "6px 14px",
                                            borderRadius: "8px",
                                            border: "2px solid #0284c7",
                                            background: "#f0f9ff",
                                            color: "#0369a1",
                                            fontWeight: "800",
                                            fontSize: "13px",
                                            outline: "none",
                                            cursor: "pointer",
                                            boxShadow: "0 1px 3px rgba(2,132,199,0.15)"
                                        }}
                                    >
                                        {strategiesList.map(strat => (
                                            <option key={strat.id} value={strat.id}>
                                                {strat.badge || strat.title} — {strat.title}
                                            </option>
                                        ))}
                                    </select>
                                    <span style={{ background: "#e0f2fe", color: "#0369a1", fontSize: "11px", fontWeight: "700", padding: "3px 8px", borderRadius: "8px" }}>
                                        {activeStrategyInfo?.category}
                                    </span>
                                </div>
                                <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#64748b" }}>
                                    {activeStrategyInfo?.shortDescription}
                                </p>
                            </div>
                        </div>

                        <button 
                            onClick={() => setShowStrategyWriteup(p => !p)}
                            style={{
                                background: showStrategyWriteup ? "#f1f5f9" : "#0284c7",
                                color: showStrategyWriteup ? "#334155" : "white",
                                border: "none",
                                borderRadius: "6px",
                                padding: "6px 12px",
                                fontSize: "12px",
                                fontWeight: "700",
                                cursor: "pointer",
                                display: "flex",
                                alignItems: "center",
                                gap: "6px"
                            }}
                        >
                            <span>{showStrategyWriteup ? "▲ Hide Trigger Rules" : "▼ View Strategy Logic & Triggers"}</span>
                        </button>
                    </div>

                    {/* Strategy Rules & Writeup */}
                    {showStrategyWriteup && activeStrategyInfo?.writeup && (
                        <div style={{ marginTop: "16px", paddingTop: "14px", borderTop: "1px solid #f1f5f9", display: "flex", flexDirection: "column", gap: "14px" }}>
                            <div style={{ background: "#f8fafc", padding: "10px 14px", borderRadius: "8px", borderLeft: "4px solid #0284c7" }}>
                                <span style={{ fontSize: "11px", fontWeight: "700", color: "#0284c7", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                                    💡 Strategy Thesis & Philosophy
                                </span>
                                <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#334155", lineHeight: "1.5" }}>
                                    {activeStrategyInfo.writeup.philosophy}
                                </p>
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px" }}>
                                {/* BUY Rules */}
                                <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "8px", padding: "12px 14px" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
                                        <span style={{ fontSize: "14px" }}>🟢</span>
                                        <span style={{ fontSize: "12px", fontWeight: "800", color: "#15803d", textTransform: "uppercase" }}>
                                            When BUY Signals Are Generated
                                        </span>
                                    </div>
                                    <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "11px", color: "#166534", lineHeight: "1.5" }}>
                                        {activeStrategyInfo.writeup.buyRules?.map((r, i) => (
                                            <li key={i} style={{ marginBottom: "4px" }}>{r}</li>
                                        ))}
                                    </ul>
                                </div>

                                {/* SELL Rules */}
                                <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "8px", padding: "12px 14px" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
                                        <span style={{ fontSize: "14px" }}>🔴</span>
                                        <span style={{ fontSize: "12px", fontWeight: "800", color: "#b91c1c", textTransform: "uppercase" }}>
                                            When SELL & Target Exits Occur
                                        </span>
                                    </div>
                                    <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "11px", color: "#991b1b", lineHeight: "1.5" }}>
                                        {activeStrategyInfo.writeup.sellRules?.map((r, i) => (
                                            <li key={i} style={{ marginBottom: "4px" }}>{r}</li>
                                        ))}
                                    </ul>
                                </div>

                                {/* STOP LOSS Rules */}
                                <div style={{ background: "#fffbeb", border: "1px solid #fde68a", borderRadius: "8px", padding: "12px 14px" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
                                        <span style={{ fontSize: "14px" }}>🛡️</span>
                                        <span style={{ fontSize: "12px", fontWeight: "800", color: "#b45309", textTransform: "uppercase" }}>
                                            Stop Loss & Risk Management
                                        </span>
                                    </div>
                                    <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "11px", color: "#92400e", lineHeight: "1.5" }}>
                                        {activeStrategyInfo.writeup.stopLossRules?.map((r, i) => (
                                            <li key={i} style={{ marginBottom: "4px" }}>{r}</li>
                                        ))}
                                    </ul>
                                </div>
                            </div>

                            {activeStrategyInfo.writeup.idealMarket && (
                                <div style={{ fontSize: "11px", color: "#64748b", display: "flex", alignItems: "center", gap: "6px" }}>
                                    <strong style={{ color: "#334155" }}>🎯 Ideal Market Environment:</strong>
                                    <span>{activeStrategyInfo.writeup.idealMarket}</span>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* 4. Main Matrix Table */}
            <div className="content-split" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                
                <div className="grid-container" style={{ background: "white", padding: "24px 28px", borderRadius: "14px", boxShadow: "0 2px 8px rgba(0,0,0,0.08)", border: "1px solid #e2e8f0", height: "auto", minHeight: "unset", width: "100%" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                        <div>
                            <h3 style={{ margin: 0, fontSize: "18px", fontWeight: "800", color: "#0f172a" }}>
                                {activeTab === "fundamentals" ? "Fundamental Analysis Matrix" : `Quant Strategy Matrix (${activeStrategyInfo?.title})`}
                            </h3>
                            <span style={{ fontSize: "13px", color: "#64748b" }}>
                                {activeTab === "fundamentals" 
                                    ? "P/E valuation vs historical medians, quarterly EPS growth, and institutional patterns • Click any row to inspect" 
                                    : `Live trade execution signals, Target, Stop Loss, and Risk:Reward for ${activeStrategyInfo?.title} • Click any row to inspect`}
                            </span>
                        </div>
                    </div>

                    <div className="ag-theme-alpine" style={{ width: "100%", height: "auto" }}>
                        <AgGridReact
                            ref={gridRef}
                            rowData={analysisData}
                            columnDefs={columnDefs}
                            rowHeight={74}
                            headerHeight={50}
                            domLayout="autoHeight"
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
                            onGridReady={(params) => {
                                setTimeout(() => params.api.sizeColumnsToFit(), 50);
                            }}
                            onGridSizeChanged={(params) => {
                                params.api.sizeColumnsToFit();
                            }}
                            onFirstDataRendered={(params) => {
                                params.api.sizeColumnsToFit();
                            }}
                            onRowClicked={handleRowClick}
                            rowSelection="single"
                            overlayNoRowsTemplate="<span style='color: #64748b; font-size: 15px; font-weight: 600;'>No stocks analyzed yet. Enter a scrip name above and click Analyze!</span>"
                        />
                    </div>
                </div>

                {/* 5. Selected Stock Deep-Dive Analytics (Strict Tab Separation) */}
                {selectedStock && (
                    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                        
                        {/* ══════════════════════════════════════════════════════════════════════
                            TAB 1: FUNDAMENTALS & HEALTH ONLY
                            (Checklist, S/R & POC, EPS Trend, Ownership)
                        ══════════════════════════════════════════════════════════════════════ */}
                        {activeTab === "fundamentals" && (
                            <>
                                {/* 1. 4-Point Health Checklist */}
                                {selectedStock.ratingChecks && (
                                    <div style={{ background: "white", padding: "18px 20px", borderRadius: "12px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)", border: "1px solid #e2e8f0" }}>
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "10px" }}>
                                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                                <span style={{ fontSize: "16px", fontWeight: "700", color: "#0f172a" }}>
                                                    {selectedStock.stock} — 4-Point Health Checklist
                                                </span>
                                                <span style={{
                                                    background: selectedStock.ratingScore === 4 ? "#dcfce7" : selectedStock.ratingScore === 3 ? "#e0f2fe" : selectedStock.ratingScore === 2 ? "#fef3c7" : "#fee2e2",
                                                    color: selectedStock.ratingScore === 4 ? "#15803d" : selectedStock.ratingScore === 3 ? "#0369a1" : selectedStock.ratingScore === 2 ? "#b45309" : "#b91c1c",
                                                    padding: "3px 10px",
                                                    borderRadius: "12px",
                                                    fontWeight: "800",
                                                    fontSize: "13px"
                                                }}>
                                                    {selectedStock.ratingScore === 4 && "⭐ "}Score: {selectedStock.ratingScore ?? 0}/4
                                                </span>
                                            </div>
                                            <span style={{ fontSize: "12px", color: "#64748b" }}>
                                                Passing {selectedStock.ratingScore ?? 0} of 4 investment criteria
                                            </span>
                                        </div>

                                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: "12px" }}>
                                            <div style={{ background: selectedStock.ratingChecks?.fiiHolding?.passed ? "#f0fdf4" : "#fef2f2", border: `1px solid ${selectedStock.ratingChecks?.fiiHolding?.passed ? "#bbf7d0" : "#fecaca"}`, borderRadius: "8px", padding: "10px 14px" }}>
                                                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                                                    <span style={{ fontWeight: "700", fontSize: "13px", color: "#1e293b" }}>1. FII Peak Holding</span>
                                                    <span style={{ fontSize: "12px", fontWeight: "700", color: selectedStock.ratingChecks?.fiiHolding?.passed ? "#15803d" : "#b91c1c" }}>
                                                        {selectedStock.ratingChecks?.fiiHolding?.passed ? "✅ PASS" : "❌ FAIL"}
                                                    </span>
                                                </div>
                                                <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "4px" }}>Max holding vs prior 2 qtrs</div>
                                                <div style={{ fontSize: "12px", fontWeight: "600", color: "#0f172a" }}>{selectedStock.ratingChecks?.fiiHolding?.detail || "—"}</div>
                                            </div>

                                            <div style={{ background: selectedStock.ratingChecks?.peValuation?.passed ? "#f0fdf4" : "#fef2f2", border: `1px solid ${selectedStock.ratingChecks?.peValuation?.passed ? "#bbf7d0" : "#fecaca"}`, borderRadius: "8px", padding: "10px 14px" }}>
                                                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                                                    <span style={{ fontWeight: "700", fontSize: "13px", color: "#1e293b" }}>2. P/E vs Medians</span>
                                                    <span style={{ fontSize: "12px", fontWeight: "700", color: selectedStock.ratingChecks?.peValuation?.passed ? "#15803d" : "#b91c1c" }}>
                                                        {selectedStock.ratingChecks?.peValuation?.passed ? "✅ PASS" : "❌ FAIL"}
                                                    </span>
                                                </div>
                                                <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "4px" }}>P/E &lt; 1Y, 3Y, 5Y Medians</div>
                                                <div style={{ fontSize: "12px", fontWeight: "600", color: "#0f172a" }}>{selectedStock.ratingChecks?.peValuation?.detail || "—"}</div>
                                            </div>

                                            <div style={{ background: selectedStock.ratingChecks?.rsiMomentum?.passed ? "#f0fdf4" : "#fef2f2", border: `1px solid ${selectedStock.ratingChecks?.rsiMomentum?.passed ? "#bbf7d0" : "#fecaca"}`, borderRadius: "8px", padding: "10px 14px" }}>
                                                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                                                    <span style={{ fontWeight: "700", fontSize: "13px", color: "#1e293b" }}>3. RSI (14) Momentum</span>
                                                    <span style={{ fontSize: "12px", fontWeight: "700", color: selectedStock.ratingChecks?.rsiMomentum?.passed ? "#15803d" : "#b91c1c" }}>
                                                        {selectedStock.ratingChecks?.rsiMomentum?.passed ? "✅ PASS" : "❌ FAIL"}
                                                    </span>
                                                </div>
                                                <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "4px" }}>RSI ≤ 55 (Entry zone)</div>
                                                <div style={{ fontSize: "12px", fontWeight: "600", color: "#0f172a" }}>{selectedStock.ratingChecks?.rsiMomentum?.detail || "—"}</div>
                                            </div>

                                            <div style={{ background: selectedStock.ratingChecks?.epsGrowth?.passed ? "#f0fdf4" : "#fef2f2", border: `1px solid ${selectedStock.ratingChecks?.epsGrowth?.passed ? "#bbf7d0" : "#fecaca"}`, borderRadius: "8px", padding: "10px 14px" }}>
                                                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                                                    <span style={{ fontWeight: "700", fontSize: "13px", color: "#1e293b" }}>4. Consistent QoQ EPS</span>
                                                    <span style={{ fontSize: "12px", fontWeight: "700", color: selectedStock.ratingChecks?.epsGrowth?.passed ? "#15803d" : "#b91c1c" }}>
                                                        {selectedStock.ratingChecks?.epsGrowth?.passed ? "✅ PASS" : "❌ FAIL"}
                                                    </span>
                                                </div>
                                                <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "4px" }}>QoQ growth across ≥ 3 of last 4 qtrs</div>
                                                <div style={{ fontSize: "12px", fontWeight: "600", color: "#0f172a" }}>{selectedStock.ratingChecks?.epsGrowth?.detail || "—"}</div>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* 2. Support, Resistance & Robust Volume Profile POC */}
                                {(selectedStock.supports?.length > 0 || selectedStock.resistances?.length > 0) && (
                                    <div style={{ background: "white", borderRadius: "12px", padding: "16px 20px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)", border: "1px solid #e2e8f0" }}>
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                                <span style={{ fontSize: "16px" }}>📐</span>
                                                <h3 style={{ margin: 0, fontSize: "15px", fontWeight: "700", color: "#0f172a" }}>
                                                    {selectedStock.stock} — Support & Resistance Zones
                                                </h3>
                                            </div>
                                            <span style={{ fontSize: "12px", color: "#64748b" }}>
                                                Current Price: <strong style={{ color: "#0f172a" }}>₹{selectedStock.currentPrice?.toLocaleString("en-IN") || "—"}</strong>
                                            </span>
                                        </div>

                                        {selectedStock.poc && (
                                            <div style={{
                                                display: "flex", alignItems: "center", justifyContent: "space-between",
                                                padding: "10px 14px", marginBottom: "12px", borderRadius: "8px",
                                                background: "linear-gradient(135deg, #fef9c3, #fefce8)",
                                                border: "2px solid #fbbf24",
                                            }}>
                                                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                                    <span style={{ fontSize: "18px" }}>🎯</span>
                                                    <div>
                                                        <div style={{ fontWeight: "800", fontSize: "14px", color: "#92400e" }}>
                                                            Volume Profile POC — ₹{selectedStock.poc.price?.toLocaleString("en-IN")}
                                                        </div>
                                                        <div style={{ fontSize: "11px", color: "#b45309" }}>
                                                            Highest traded volume price over past year — strongest institutional S/R level
                                                            {selectedStock.poc.roundNumber ? " 🔵 Round number" : ""}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div style={{ textAlign: "right" }}>
                                                    <div style={{
                                                        padding: "3px 10px", borderRadius: "6px", fontSize: "12px", fontWeight: "700",
                                                        background: selectedStock.poc.side === "support" ? "#dcfce7" : "#fee2e2",
                                                        color: selectedStock.poc.side === "support" ? "#15803d" : "#dc2626",
                                                    }}>
                                                        {selectedStock.poc.side === "support" ? "🟢 Below CMP" : "🔴 Above CMP"}
                                                    </div>
                                                    <div style={{ fontSize: "10px", color: "#78716c", marginTop: "3px" }}>
                                                        {selectedStock.currentPrice
                                                            ? `${(((selectedStock.poc.price - selectedStock.currentPrice) / selectedStock.currentPrice) * 100).toFixed(1)}% from CMP`
                                                            : ""}
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                                            <div>
                                                <div style={{ fontSize: "11px", fontWeight: "700", color: "#15803d", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                                                    🟢 Support Levels
                                                </div>
                                                {(selectedStock.supports || []).map((s, idx) => {
                                                    const dist = selectedStock.currentPrice ? ((s.price - selectedStock.currentPrice) / selectedStock.currentPrice * 100) : null;
                                                    const stars = "★".repeat(Math.min(s.strength, 4));
                                                    const nearBuy = dist !== null && dist >= -3;
                                                    return (
                                                        <div key={idx} style={{
                                                            display: "flex", alignItems: "center", justifyContent: "space-between",
                                                            padding: "6px 10px", marginBottom: "4px", borderRadius: "6px",
                                                            background: nearBuy ? "#f0fdf4" : "#f8fafc",
                                                            border: `1px solid ${nearBuy ? "#bbf7d0" : "#e2e8f0"}`,
                                                        }}>
                                                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                                                <span style={{ fontWeight: "700", fontSize: "13px", color: nearBuy ? "#15803d" : "#1e293b" }}>
                                                                    S{idx + 1}: ₹{s.price.toLocaleString("en-IN")}
                                                                </span>
                                                                <span style={{ fontSize: "11px", color: "#f59e0b" }}>{stars}</span>
                                                            </div>
                                                            <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                                                                {dist !== null && (
                                                                    <span style={{
                                                                        fontSize: "11px", fontWeight: "700", padding: "1px 5px", borderRadius: "4px",
                                                                        background: nearBuy ? "#dcfce7" : "#f1f5f9",
                                                                        color: nearBuy ? "#15803d" : "#64748b"
                                                                    }}>{dist.toFixed(1)}%</span>
                                                                )}
                                                                {s.roleReversal && <span title="Role Reversal" style={{ fontSize: "11px" }}>↩</span>}
                                                                {s.volumeConfirmed && <span title="Volume Confirmed" style={{ fontSize: "11px" }}>📊</span>}
                                                                {s.roundNumber && <span title="Round Number" style={{ fontSize: "11px" }}>🔵</span>}
                                                                <span style={{ fontSize: "10px", color: "#94a3b8" }}>{s.touchCount}×</span>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>

                                            <div>
                                                <div style={{ fontSize: "11px", fontWeight: "700", color: "#dc2626", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                                                    🔴 Resistance Levels
                                                </div>
                                                {(selectedStock.resistances || []).map((r, idx) => {
                                                    const dist = selectedStock.currentPrice ? ((r.price - selectedStock.currentPrice) / selectedStock.currentPrice * 100) : null;
                                                    const stars = "★".repeat(Math.min(r.strength, 4));
                                                    return (
                                                        <div key={idx} style={{
                                                            display: "flex", alignItems: "center", justifyContent: "space-between",
                                                            padding: "6px 10px", marginBottom: "4px", borderRadius: "6px",
                                                            background: "#fef9f9",
                                                            border: "1px solid #fecaca",
                                                        }}>
                                                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                                                <span style={{ fontWeight: "700", fontSize: "13px", color: "#dc2626" }}>
                                                                    R{idx + 1}: ₹{r.price.toLocaleString("en-IN")}
                                                                </span>
                                                                <span style={{ fontSize: "11px", color: "#f59e0b" }}>{stars}</span>
                                                            </div>
                                                            <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                                                                {dist !== null && (
                                                                    <span style={{
                                                                        fontSize: "11px", fontWeight: "700", padding: "1px 5px", borderRadius: "4px",
                                                                        background: "#fef2f2", color: "#b91c1c"
                                                                    }}>+{dist.toFixed(1)}%</span>
                                                                )}
                                                                {r.roleReversal && <span title="Role Reversal" style={{ fontSize: "11px" }}>↩</span>}
                                                                {r.volumeConfirmed && <span title="Volume Confirmed" style={{ fontSize: "11px" }}>📊</span>}
                                                                {r.roundNumber && <span title="Round Number" style={{ fontSize: "11px" }}>🔵</span>}
                                                                <span style={{ fontSize: "10px", color: "#94a3b8" }}>{r.touchCount}×</span>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* 3. Quarterly EPS & Ownership Charts */}
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
                                            <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                                                <span style={{ background: "#f1f5f9", padding: "4px 10px", borderRadius: "6px", fontSize: "12px", fontWeight: "700", color: "#0284c7" }}>
                                                    P/E: {selectedStock.peRatio ? `${selectedStock.peRatio}x` : "—"}
                                                </span>
                                                {selectedStock.peMedian1Y != null && (
                                                    <span style={{ padding: "4px 8px", borderRadius: "6px", fontSize: "11px", fontWeight: "700", background: selectedStock.belowMedian1Y ? "#dcfce7" : "#fee2e2", color: selectedStock.belowMedian1Y ? "#15803d" : "#b91c1c" }}>
                                                        1Y {selectedStock.belowMedian1Y ? "↓" : "↑"} {selectedStock.peMedian1Y}x
                                                    </span>
                                                )}
                                                {selectedStock.peMedian3Y != null && (
                                                    <span style={{ padding: "4px 8px", borderRadius: "6px", fontSize: "11px", fontWeight: "700", background: selectedStock.belowMedian3Y ? "#dcfce7" : "#fee2e2", color: selectedStock.belowMedian3Y ? "#15803d" : "#b91c1c" }}>
                                                        3Y {selectedStock.belowMedian3Y ? "↓" : "↑"} {selectedStock.peMedian3Y}x
                                                    </span>
                                                )}
                                                {selectedStock.peMedian5Y != null && (
                                                    <span style={{ padding: "4px 8px", borderRadius: "6px", fontSize: "11px", fontWeight: "700", background: selectedStock.belowMedian5Y ? "#dcfce7" : "#fee2e2", color: selectedStock.belowMedian5Y ? "#15803d" : "#b91c1c" }}>
                                                        5Y {selectedStock.belowMedian5Y ? "↓" : "↑"} {selectedStock.peMedian5Y}x
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        {epsChartData.length > 0 ? (
                                            <ResponsiveContainer width="100%" height={220}>
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
                                            <div style={{ height: "220px", display: "flex", alignItems: "center", justifyContent: "center", color: "#94a3b8" }}>
                                                No quarterly EPS data available for {selectedStock.stock}
                                            </div>
                                        )}
                                    </div>

                                    {/* Shareholding Breakdown */}
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
                                            <ResponsiveContainer width="100%" height={220}>
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
                                            <div style={{ height: "220px", display: "flex", alignItems: "center", justifyContent: "center", color: "#94a3b8" }}>
                                                No shareholding pattern available for {selectedStock.stock}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </>
                        )}

                        {/* ══════════════════════════════════════════════════════════════════════
                            TAB 2: QUANT STRATEGIES & BACKTESTS ONLY
                            (Live Signal Card + 2-Year Walk-Forward Simulation)
                        ══════════════════════════════════════════════════════════════════════ */}
                        {activeTab === "strategies" && (
                            <>
                                {/* 1. Live Signal & Target Calculator Card */}
                                <div style={{ background: "white", borderRadius: "12px", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)", display: "flex", flexDirection: "column", gap: "16px", border: "1px solid #e2e8f0" }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                            <span style={{ fontSize: "22px" }}>🎯</span>
                                            <div>
                                                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                                    <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "700", color: "#0f172a" }}>
                                                        {selectedStock.stock} — Live Execution Signal ({activeStrategyInfo?.title})
                                                    </h3>
                                                    {currentStockSignal?.signal && (
                                                        <span style={{
                                                            padding: "3px 12px", borderRadius: "12px", fontSize: "12px", fontWeight: "800",
                                                            background: currentStockSignal.signal === "BUY" ? "#dcfce7" : (currentStockSignal.signal === "SELL" ? "#fee2e2" : "#f1f5f9"),
                                                            color: currentStockSignal.signal === "BUY" ? "#15803d" : (currentStockSignal.signal === "SELL" ? "#b91c1c" : "#475569"),
                                                            border: `1px solid ${currentStockSignal.signal === "BUY" ? "#86efac" : (currentStockSignal.signal === "SELL" ? "#fca5a5" : "#cbd5e1")}`
                                                        }}>
                                                            {currentStockSignal.signalBadge || (currentStockSignal.signal === "BUY" ? "🟢 BUY" : (currentStockSignal.signal === "SELL" ? "🔴 SELL" : "⚪ HOLD"))}
                                                        </span>
                                                    )}
                                                </div>
                                                <p style={{ margin: "3px 0 0 0", color: "#64748b", fontSize: "12px" }}>
                                                    {currentStockSignal?.reason || "Live trade stance based on active quantitative model"}
                                                </p>
                                            </div>
                                        </div>

                                        {/* Target & SL Badges */}
                                        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
                                            <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", padding: "6px 14px", borderRadius: "8px", textAlign: "center" }}>
                                                <div style={{ fontSize: "10px", fontWeight: "700", color: "#15803d", textTransform: "uppercase" }}>🎯 Target</div>
                                                <div style={{ fontSize: "15px", fontWeight: "800", color: "#15803d" }}>
                                                    {currentStockSignal?.targetPrice ? `₹${currentStockSignal.targetPrice.toLocaleString("en-IN")}` : "—"}
                                                </div>
                                                {selectedStock.currentPrice && currentStockSignal?.targetPrice && (
                                                    <div style={{ fontSize: "10px", color: "#16a34a", fontWeight: "700" }}>
                                                        +{(((currentStockSignal.targetPrice - selectedStock.currentPrice) / selectedStock.currentPrice) * 100).toFixed(1)}%
                                                    </div>
                                                )}
                                            </div>

                                            <div style={{ background: "#fef2f2", border: "1px solid #fecaca", padding: "6px 14px", borderRadius: "8px", textAlign: "center" }}>
                                                <div style={{ fontSize: "10px", fontWeight: "700", color: "#b91c1c", textTransform: "uppercase" }}>🛡️ Stop Loss</div>
                                                <div style={{ fontSize: "15px", fontWeight: "800", color: "#b91c1c" }}>
                                                    {currentStockSignal?.stopLossPrice ? `₹${currentStockSignal.stopLossPrice.toLocaleString("en-IN")}` : "—"}
                                                </div>
                                                {selectedStock.currentPrice && currentStockSignal?.stopLossPrice && (
                                                    <div style={{ fontSize: "10px", color: "#dc2626", fontWeight: "700" }}>
                                                        {(((currentStockSignal.stopLossPrice - selectedStock.currentPrice) / selectedStock.currentPrice) * 100).toFixed(1)}%
                                                    </div>
                                                )}
                                            </div>

                                            {currentStockSignal?.riskRewardRatio && (
                                                <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", padding: "6px 14px", borderRadius: "8px", textAlign: "center" }}>
                                                    <div style={{ fontSize: "10px", fontWeight: "700", color: "#475569", textTransform: "uppercase" }}>⚖️ Risk / Reward</div>
                                                    <div style={{ fontSize: "15px", fontWeight: "800", color: "#0f172a" }}>
                                                        1 : {currentStockSignal.riskRewardRatio}
                                                    </div>
                                                    <div style={{ fontSize: "10px", color: "#64748b" }}>Risk-adjusted</div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* 2. 2-Year Walk-Forward Strategy Backtest Simulation */}
                                <div style={{ background: "white", borderRadius: "12px", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)", display: "flex", flexDirection: "column", gap: "16px", border: "1px solid #e2e8f0" }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
                                        <div>
                                            <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "700", color: "#0f172a" }}>
                                                📈 {selectedStock.stock} — 2-Year Simulation: {activeStrategyInfo?.title}
                                            </h3>
                                            <span style={{ fontSize: "12px", color: "#64748b" }}>
                                                Historical walk-forward trade simulation (₹1,00,000 initial capital)
                                            </span>
                                        </div>
                                    </div>

                                    {backtestLoading ? (
                                        <div style={{ padding: "30px", textAlign: "center", color: "#64748b", fontSize: "13px" }}>
                                            ⏳ Running 2-year simulation ({activeStrategyInfo?.title}) for {selectedStock.stock}...
                                        </div>
                                    ) : backtestData?.summary ? (
                                        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                                            {/* KPI Summary Cards */}
                                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: "10px" }}>
                                                <div style={{ background: backtestData.summary.strategyReturnPct >= 0 ? "#f0fdf4" : "#fef2f2", border: `1px solid ${backtestData.summary.strategyReturnPct >= 0 ? "#bbf7d0" : "#fecaca"}`, borderRadius: "8px", padding: "10px 14px" }}>
                                                    <div style={{ fontSize: "11px", fontWeight: "600", color: "#64748b" }}>Strategy Total PnL</div>
                                                    <div style={{ fontSize: "18px", fontWeight: "800", color: backtestData.summary.strategyReturnPct >= 0 ? "#15803d" : "#b91c1c", marginTop: "2px" }}>
                                                        {backtestData.summary.strategyReturnPct >= 0 ? "+" : ""}{backtestData.summary.strategyReturnPct}%
                                                    </div>
                                                    <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>
                                                        Buy & Hold: {backtestData.summary.buyAndHoldReturnPct >= 0 ? "+" : ""}{backtestData.summary.buyAndHoldReturnPct}%
                                                    </div>
                                                </div>

                                                <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "10px 14px" }}>
                                                    <div style={{ fontSize: "11px", fontWeight: "600", color: "#64748b" }}>Win Rate</div>
                                                    <div style={{ fontSize: "18px", fontWeight: "800", color: backtestData.summary.winRatePct >= 50 ? "#15803d" : "#b91c1c", marginTop: "2px" }}>
                                                        {backtestData.summary.winRatePct}%
                                                    </div>
                                                    <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>
                                                        {backtestData.summary.winningTrades} Wins / {backtestData.summary.losingTrades} Losses
                                                    </div>
                                                </div>

                                                <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "10px 14px" }}>
                                                    <div style={{ fontSize: "11px", fontWeight: "600", color: "#64748b" }}>Profit Factor</div>
                                                    <div style={{ fontSize: "18px", fontWeight: "800", color: backtestData.summary.profitFactor >= 1.5 ? "#15803d" : (backtestData.summary.profitFactor >= 1.0 ? "#0284c7" : "#b91c1c"), marginTop: "2px" }}>
                                                        {backtestData.summary.profitFactor}
                                                    </div>
                                                    <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>
                                                        Gross Profit / Loss
                                                    </div>
                                                </div>

                                                <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "10px 14px" }}>
                                                    <div style={{ fontSize: "11px", fontWeight: "600", color: "#64748b" }}>Max Drawdown</div>
                                                    <div style={{ fontSize: "18px", fontWeight: "800", color: "#b91c1c", marginTop: "2px" }}>
                                                        -{backtestData.summary.maxDrawdownPct}%
                                                    </div>
                                                    <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>
                                                        Peak-to-Trough
                                                    </div>
                                                </div>

                                                <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "10px 14px" }}>
                                                    <div style={{ fontSize: "11px", fontWeight: "600", color: "#64748b" }}>Total Trades</div>
                                                    <div style={{ fontSize: "18px", fontWeight: "800", color: "#0f172a", marginTop: "2px" }}>
                                                        {backtestData.summary.totalTrades}
                                                    </div>
                                                    <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>
                                                        Avg {backtestData.summary.avgHoldingDays} days / trade
                                                    </div>
                                                </div>
                                            </div>

                                            {/* 2-Year Equity Comparison Chart */}
                                            {backtestData.equityCurve?.length > 0 && (
                                                <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "14px" }}>
                                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                                                        <span style={{ fontSize: "12px", fontWeight: "700", color: "#1e293b" }}>
                                                            📈 2-Year Growth of ₹1,00,000 ({activeStrategyInfo?.title} vs Buy & Hold)
                                                        </span>
                                                        <div style={{ display: "flex", gap: "12px", fontSize: "11px" }}>
                                                            <span style={{ color: "#0284c7", fontWeight: "700" }}>● {activeStrategyInfo?.title}</span>
                                                            <span style={{ color: "#94a3b8", fontWeight: "700" }}>● Buy & Hold</span>
                                                        </div>
                                                    </div>
                                                    <div style={{ height: "180px", width: "100%" }}>
                                                        <ResponsiveContainer width="100%" height="100%">
                                                            <LineChart data={backtestData.equityCurve} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                                                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                                                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#64748b" }} tickFormatter={d => d.slice(2, 7)} />
                                                                <YAxis tick={{ fontSize: 10, fill: "#64748b" }} tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} />
                                                                <Tooltip
                                                                    formatter={(val, name) => [`₹${Number(val).toLocaleString("en-IN")}`, name === "strategy" ? activeStrategyInfo?.title : "Buy & Hold"]}
                                                                    labelFormatter={l => `Date: ${l}`}
                                                                    contentStyle={{ borderRadius: "8px", border: "1px solid #cbd5e1", fontSize: "11px" }}
                                                                />
                                                                <Line type="monotone" dataKey="strategy" stroke="#0284c7" strokeWidth={2.5} dot={false} name="strategy" />
                                                                <Line type="monotone" dataKey="benchmark" stroke="#94a3b8" strokeWidth={1.5} strokeDasharray="3 3" dot={false} name="benchmark" />
                                                            </LineChart>
                                                        </ResponsiveContainer>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Completed Trades Log Toggle */}
                                            <div>
                                                <button
                                                    onClick={() => setShowTradeLog(prev => !prev)}
                                                    style={{
                                                        background: "none", border: "1px solid #cbd5e1", borderRadius: "6px",
                                                        padding: "6px 12px", fontSize: "12px", fontWeight: "600", color: "#0284c7",
                                                        cursor: "pointer", display: "inline-flex", alignItems: "center", gap: "6px"
                                                    }}
                                                >
                                                    <span>{showTradeLog ? "▼ Hide" : "▶ View"} Completed Trades ({backtestData.trades?.length || 0})</span>
                                                </button>

                                                {showTradeLog && backtestData.trades?.length > 0 && (
                                                    <div style={{ marginTop: "10px", maxHeight: "240px", overflowY: "auto", border: "1px solid #e2e8f0", borderRadius: "8px" }}>
                                                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px", textAlign: "left" }}>
                                                            <thead>
                                                                <tr style={{ background: "#f1f5f9", borderBottom: "1px solid #cbd5e1", color: "#475569" }}>
                                                                    <th style={{ padding: "6px 10px" }}>#</th>
                                                                    <th style={{ padding: "6px 10px" }}>Entry Date</th>
                                                                    <th style={{ padding: "6px 10px" }}>Entry ₹</th>
                                                                    <th style={{ padding: "6px 10px" }}>Exit Date</th>
                                                                    <th style={{ padding: "6px 10px" }}>Exit ₹</th>
                                                                    <th style={{ padding: "6px 10px" }}>Days</th>
                                                                    <th style={{ padding: "6px 10px" }}>PnL %</th>
                                                                    <th style={{ padding: "6px 10px" }}>Exit Reason</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody>
                                                                {backtestData.trades.map((t, idx) => (
                                                                    <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9", background: idx % 2 === 0 ? "white" : "#fafafa" }}>
                                                                        <td style={{ padding: "6px 10px", color: "#64748b" }}>{idx + 1}</td>
                                                                        <td style={{ padding: "6px 10px", fontWeight: "600" }}>{t.entryDate}</td>
                                                                        <td style={{ padding: "6px 10px" }}>₹{t.entryPrice?.toLocaleString("en-IN")}</td>
                                                                        <td style={{ padding: "6px 10px", fontWeight: "600" }}>{t.exitDate}</td>
                                                                        <td style={{ padding: "6px 10px" }}>₹{t.exitPrice?.toLocaleString("en-IN")}</td>
                                                                        <td style={{ padding: "6px 10px", color: "#64748b" }}>{t.holdingDays}d</td>
                                                                        <td style={{ padding: "6px 10px", fontWeight: "700", color: t.pnlPct >= 0 ? "#15803d" : "#b91c1c" }}>
                                                                            {t.pnlPct >= 0 ? "+" : ""}{t.pnlPct}%
                                                                        </td>
                                                                        <td style={{ padding: "6px 10px", color: "#475569" }}>
                                                                            <span style={{
                                                                                padding: "1px 6px", borderRadius: "4px", fontSize: "10px", fontWeight: "600",
                                                                                background: t.pnlPct >= 0 ? "#dcfce7" : "#fee2e2",
                                                                                color: t.pnlPct >= 0 ? "#15803d" : "#b91c1c"
                                                                            }}>
                                                                                {t.reason}
                                                                            </span>
                                                                        </td>
                                                                    </tr>
                                                                ))}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        <div style={{ padding: "16px", textAlign: "center", color: "#94a3b8", fontSize: "12px" }}>
                                            No simulation available for this stock.
                                        </div>
                                    )}
                                </div>
                            </>
                        )}

                    </div>
                )}
            </div>
        </div>
    );
};

export default AnalysisUI;
