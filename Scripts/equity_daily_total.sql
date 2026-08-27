WITH BaseAgg AS (
    SELECT
        pos.asOfDate,
        SUM(pos.totalInvestment)                            AS totalPortfolioCost,
        SUM(pos.currentInvestment)                          AS totalPortfolioValue,
        SUM(pos.currentInvestment - pos.totalInvestment)    AS totalCumulativePnL,
        ROUND(
            CAST(SUM(pos.currentInvestment - pos.totalInvestment) AS FLOAT) /
            NULLIF(SUM(pos.totalInvestment), 0) * 100
        , 2)                                                AS overallPnLPct
    FROM Equity_DayWisePosition pos
    -- Join added to access userName for filtering
    JOIN USERS u ON pos.userId = u.id 
    WHERE u.userName != 'Combined'
    GROUP BY pos.asOfDate
),
WithDailyPnL AS (
    SELECT
        asOfDate,
        totalPortfolioCost,
        totalPortfolioValue,
        totalCumulativePnL,
        overallPnLPct,

        -- Daily PnL: change in value minus change in cost
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

        -- Week-over-week
        totalPortfolioValue
            - LAG(totalPortfolioValue, 7) OVER (ORDER BY asOfDate)
                                                            AS weeklyPnL,

        LAG(totalPortfolioValue, 7) OVER (ORDER BY asOfDate)
                                                            AS prevWeekValue,

        -- Peak value for drawdown
        MAX(totalPortfolioValue) OVER (
            ORDER BY asOfDate
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                                                   AS peakValue

    FROM BaseAgg
),
WithAllMetrics AS (
    SELECT
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

        -- Safe to aggregate now: dailyPnL is a plain column
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