WITH EquityDaily AS (
    SELECT
        pos.asOfDate,
        SUM(pos.totalInvestment)                            AS eqCost,
        SUM(pos.currentInvestment)                          AS eqVal
    FROM Equity_DayWisePosition pos
    JOIN USERS u ON pos.userId = u.id
    WHERE u.userName != 'Combined'
    GROUP BY pos.asOfDate
),
MFDaily AS (
    SELECT
        pos.asOfDate,
        SUM(pos.totalInvestment)                            AS mfCost,
        SUM(pos.currentInvestment)                          AS mfVal
    FROM MF_DayWisePosition pos
    JOIN USERS u ON pos.userId = u.id
    WHERE u.userName != 'Combined'
    GROUP BY pos.asOfDate
),
BaseAgg AS (
    SELECT
        COALESCE(e.asOfDate, m.asOfDate)                    AS asOfDate,
        COALESCE(eqCost, 0) + COALESCE(mfCost, 0)           AS totalPortfolioCost,
        COALESCE(eqVal, 0)  + COALESCE(mfVal, 0)            AS totalPortfolioValue,
        (COALESCE(eqVal, 0) + COALESCE(mfVal, 0)) - 
        (COALESCE(eqCost, 0) + COALESCE(mfCost, 0))         AS totalCumulativePnL,
        ROUND(
            CAST((COALESCE(eqVal, 0) + COALESCE(mfVal, 0)) - 
                 (COALESCE(eqCost, 0) + COALESCE(mfCost, 0)) AS FLOAT) /
            NULLIF(COALESCE(eqCost, 0) + COALESCE(mfCost, 0), 0) * 100
        , 2)                                                AS overallPnLPct
    FROM EquityDaily e
    FULL OUTER JOIN MFDaily m ON e.asOfDate = m.asOfDate
),
WithDailyPnL AS (
    SELECT
        asOfDate,
        totalPortfolioCost,
        totalPortfolioValue,
        totalCumulativePnL,
        overallPnLPct,

        -- Daily PnL: Change in Value adjusted for change in Cost (Inflows/Outflows)
        (totalPortfolioValue - LAG(totalPortfolioValue) OVER (ORDER BY asOfDate)) -
        (totalPortfolioCost  - LAG(totalPortfolioCost)  OVER (ORDER BY asOfDate))
                                                            AS dailyPnL,

        ROUND(
            CAST(
                (totalPortfolioValue - LAG(totalPortfolioValue) OVER (ORDER BY asOfDate)) -
                (totalPortfolioCost  - LAG(totalPortfolioCost)  OVER (ORDER BY asOfDate))
            AS FLOAT) /
            NULLIF(LAG(totalPortfolioValue) OVER (ORDER BY asOfDate), 0) * 100
        , 2)                                                AS dailyPnLPct,

        -- Week-over-week logic
        totalPortfolioValue - LAG(totalPortfolioValue, 7) OVER (ORDER BY asOfDate)
                                                            AS weeklyPnL,
        LAG(totalPortfolioValue, 7) OVER (ORDER BY asOfDate)
                                                            AS prevWeekValue,

        -- Running Peak Value for Drawdown calculation
        MAX(totalPortfolioValue) OVER (
            ORDER BY asOfDate
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                                                   AS peakValue
    FROM BaseAgg
),
WithAllMetrics AS (
    SELECT
        *,
        MAX(dailyPnL) OVER ()                               AS bestDayPnL,
        MIN(dailyPnL) OVER ()                               AS worstDayPnL
    FROM WithDailyPnL
)
SELECT
    asOfDate,
    totalPortfolioCost,
    totalPortfolioValue,
    totalCumulativePnL,
    overallPnLPct,

    dailyPnL,
    dailyPnLPct,

    -- 7-Day Rolling Average of Daily PnL
    ROUND(
        AVG(dailyPnL) OVER (
            ORDER BY asOfDate
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )
    , 2)                                                    AS rollingAvgPnL7d,

    weeklyPnL,
    ROUND(CAST(weeklyPnL AS FLOAT) / NULLIF(prevWeekValue, 0) * 100, 2)
                                                            AS weeklyPnLPct,

    peakValue,
    ROUND(totalPortfolioValue - peakValue, 2)               AS drawdown,
    ROUND(
        CAST(totalPortfolioValue - peakValue AS FLOAT) /
        NULLIF(peakValue, 0) * 100
    , 2)                                                    AS drawdownPct,

    bestDayPnL,
    worstDayPnL

FROM WithAllMetrics
ORDER BY asOfDate DESC;