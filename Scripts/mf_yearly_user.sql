WITH YearlySnapshots AS (
    SELECT
        STRFTIME('%Y', dwp.asOfDate) AS year,
        u.username AS userName,
        SUM(dwp.totalInvestment) AS totalInvested,
        SUM(dwp.currentInvestment) AS currentVal,
        SUM(dwp.currentInvestment - dwp.totalInvestment) AS totalPnL
    FROM MF_DayWisePosition dwp 
    JOIN USERS u ON dwp.userId = u.id 
    WHERE dwp.asOfDate IN (
        SELECT MAX(d2.asOfDate)
        FROM MF_DayWisePosition d2
        GROUP BY STRFTIME('%Y', d2.asOfDate)
    )
    GROUP BY year, u.username
)
SELECT 
    year,
    userName,
    totalInvested,
    currentVal,
    totalPnL AS cumulativePnL,
    -- Yearly Change (This year-end PnL - Last year-end PnL)
    ROUND(totalPnL - LAG(totalPnL) OVER (PARTITION BY userName ORDER BY year), 2) AS yearlyChange,
    -- Yearly Change %: (Yearly Change / Current Total Invested)
    ROUND(
        (totalPnL - LAG(totalPnL) OVER (PARTITION BY userName ORDER BY year)) * 100.0 / 
        NULLIF(totalInvested, 0), 
    2) || '%' AS yearlyChangePercent
FROM YearlySnapshots
ORDER BY year DESC, userName;
