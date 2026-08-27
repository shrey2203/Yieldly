WITH MonthlySnapshots AS (
    SELECT
        STRFTIME('%Y-%m', dwp.asOfDate) AS yearMonth,
        SUM(dwp.totalInvestment) AS totalInvested,
        SUM(dwp.currentInvestment) AS currentVal,
        SUM(dwp.currentInvestment - dwp.totalInvestment) AS totalPnL,
        dwp.asOfDate AS actualDate
    FROM MF_DayWisePosition dwp 
    WHERE dwp.asOfDate IN (
        -- This logic grabs the latest date for every unique month in the table
        SELECT MAX(d2.asOfDate)
        FROM MF_DayWisePosition d2
        WHERE d2.asOfDate >= DATE('now', '-300 months')
        GROUP BY STRFTIME('%Y-%m', d2.asOfDate)
    )
    GROUP BY yearMonth
)
SELECT 
    yearMonth,
    totalInvested AS "Total Invested",
    currentVal AS "Current Value",
    totalPnL AS "Cumulative PnL",
    ROUND(totalPnL - LAG(totalPnL) OVER (ORDER BY yearMonth), 2) AS "Monthly Change",
    -- Change %
    ROUND(
        (totalPnL - LAG(totalPnL) OVER (ORDER BY yearMonth)) * 100.0 / 
        NULLIF(totalInvested, 0), 
    2) || '%' AS "Monthly Change %"
FROM MonthlySnapshots
ORDER BY yearMonth DESC;