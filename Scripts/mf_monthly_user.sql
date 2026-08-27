WITH MonthlySnapshots AS (
    SELECT
        STRFTIME('%Y-%m', dwp.asOfDate) AS yearMonth,
        u.username AS userName,
        SUM(dwp.totalInvestment) AS totalInvested,
        SUM(dwp.currentInvestment) AS currentVal,
        SUM(dwp.currentInvestment - dwp.totalInvestment) AS totalPnL
    FROM MF_DayWisePosition dwp 
    JOIN USERS u ON dwp.userId = u.id 
    WHERE dwp.asOfDate IN (
        SELECT MAX(d2.asOfDate)
        FROM MF_DayWisePosition d2
        WHERE d2.asOfDate >= DATE('now', 'start of month', '-300 months', 'localtime')
        GROUP BY STRFTIME('%Y-%m', d2.asOfDate)
    )
    GROUP BY yearMonth, u.username
)
SELECT 
    yearMonth,
    userName,
    totalInvested,
    currentVal,
    totalPnL AS cumulativePnL,
    -- Monthly Change (This month-end PnL - Last month-end PnL)
    ROUND(totalPnL - LAG(totalPnL) OVER (PARTITION BY userName ORDER BY yearMonth), 2) AS monthlyChange,
    -- Monthly Change %: (Monthly Change / Current Total Invested)
    ROUND(
        (totalPnL - LAG(totalPnL) OVER (PARTITION BY userName ORDER BY yearMonth)) * 100.0 / 
        NULLIF(totalInvested, 0), 
    2) || '%' AS monthlyChangePercent
FROM MonthlySnapshots
ORDER BY yearMonth DESC, userName;
