WITH YearlySnapshots AS (
    SELECT
        STRFTIME('%Y', dwp.asOfDate) AS year,
        SUM(dwp.totalInvestment) AS totalInvested,
        SUM(dwp.currentInvestment) AS currentVal,
        SUM(dwp.currentInvestment - dwp.totalInvestment) AS totalPnL
    FROM MF_DayWisePosition dwp 
    WHERE dwp.asOfDate IN (
        -- 1. Get the last recorded date of every full past year
        SELECT MAX(d2.asOfDate)
        FROM MF_DayWisePosition d2
        WHERE d2.asOfDate < DATE('now', 'start of year', 'localtime')
        GROUP BY STRFTIME('%Y', d2.asOfDate)
        
        UNION
        
        -- 2. Get the latest available date for the current year
        SELECT MAX(d3.asOfDate)
        FROM MF_DayWisePosition d3
        WHERE d3.asOfDate >= DATE('now', 'start of year', 'localtime')
    )
    GROUP BY year
)
SELECT 
    year,
    totalInvested AS "Total Invested",
    currentVal AS "Current Value",
    totalPnL AS "Cumulative PnL",
    ROUND(totalPnL - LAG(totalPnL) OVER (ORDER BY year), 2) AS "Yearly Change",
    ROUND((totalPnL - LAG(totalPnL) OVER (ORDER BY year)) * 100.0 / 
    NULLIF(totalInvested, 0), 2) || '%' AS "Yearly Change %"
FROM YearlySnapshots
ORDER BY year DESC;