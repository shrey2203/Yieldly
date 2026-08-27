WITH BaseAgg AS (
    SELECT
        u.userName                                          AS uName,
        pos.asOfDate,
        SUM(pos.totalInvestment)                            AS totalPortfolioCost,
        SUM(pos.currentInvestment)                          AS totalPortfolioValue,
        SUM(pos.currentInvestment - pos.totalInvestment)    AS totalCumulativePnL,
        ROUND(
            CAST(SUM(pos.currentInvestment - pos.totalInvestment) AS FLOAT) /
            NULLIF(SUM(pos.totalInvestment), 0) * 100
        , 2)                                                AS overallPnLPct
    FROM Equity_DayWisePosition pos
    JOIN USERS u ON pos.userId = u.id
    -- Added Filter Here
    WHERE u.userName != 'Combined'
    GROUP BY u.userName, pos.asOfDate
),
WithDailyPnL AS (
    SELECT
        uName,
        asOfDate,
        totalPortfolioCost,
        totalPortfolioValue,
        totalCumulativePnL,
        overallPnLPct,

        totalCumulativePnL
            - LAG(totalCumulativePnL) OVER (PARTITION BY uName ORDER BY asOfDate)
                                                            AS dailyPnL,

        ROUND(
            CAST(
                totalCumulativePnL
                - LAG(totalCumulativePnL) OVER (PARTITION BY uName ORDER BY asOfDate)
            AS FLOAT) /
            NULLIF(LAG(totalPortfolioValue) OVER (PARTITION BY uName ORDER BY asOfDate), 0) * 100
        , 2)                                                AS dailyPnLPct,

        totalPortfolioValue
            - LAG(totalPortfolioValue, 7) OVER (PARTITION BY uName ORDER BY asOfDate)
                                                            AS weeklyPnL,

        LAG(totalPortfolioValue, 7) OVER (PARTITION BY uName ORDER BY asOfDate)
                                                            AS prevWeekValue,

        MAX(totalPortfolioValue) OVER (
            PARTITION BY uName ORDER BY asOfDate
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                                                   AS peakValue

    FROM BaseAgg
),
WithAllMetrics AS (
    SELECT
        uName,
        asOfDate,
        totalPortfolioCost,
        totalPortfolioValue,
        totalCumulativePnL,
        overallPnLPct,
        dailyPnL,
        dailyPnLPct,
        weeklyPnL,
        prevWeekValue,
        peakValue,

        MAX(dailyPnL) OVER (PARTITION BY uName)             AS bestDayPnL,
        MIN(dailyPnL) OVER (PARTITION BY uName)             AS worstDayPnL

    FROM WithDailyPnL
)
SELECT
    uName,
    asOfDate,
    totalPortfolioCost,
    totalPortfolioValue,
    totalCumulativePnL,
    overallPnLPct,

    dailyPnL,
    dailyPnLPct,

    ROUND(
        AVG(dailyPnL) OVER (
            PARTITION BY uName ORDER BY asOfDate
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
ORDER BY asOfDate DESC, uName ASC;