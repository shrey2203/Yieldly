WITH DailySnapshots AS (
    SELECT
        dwp.asOfDate,
        -- Combined investment and value for all users
        SUM(dwp.totalInvestment) AS totalInvested,
        SUM(dwp.currentInvestment) AS currentVal,
        SUM(dwp.currentInvestment - dwp.totalInvestment) AS totalPnL
    FROM MF_DayWisePosition dwp 
    -- Filtering for the last 30 days of records
    WHERE dwp.asOfDate >= DATE('now', '-3000 days', 'localtime')
    GROUP BY dwp.asOfDate
)
SELECT 
    asOfDate,
    totalInvested,
    currentVal,
    totalPnL AS cumulativePnL,
    ROUND(totalPnL - LAG(totalPnL) OVER (ORDER BY asOfDate), 2) AS dailyChange,
    ROUND((totalPnL - LAG(totalPnL) OVER (ORDER BY asOfDate)) * 100.0 / 
        NULLIF(totalInvested, 0), 
    2) || '%' AS dailyChangePercent
FROM DailySnapshots
ORDER BY asOfDate DESC;
