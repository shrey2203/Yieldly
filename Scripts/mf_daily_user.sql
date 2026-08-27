WITH DailySnapshots AS (
    SELECT
        dwp.asOfDate,
        u.username AS userName,
        SUM(dwp.totalInvestment) AS totalInvested,
        SUM(dwp.currentInvestment) AS currentVal,
        SUM(dwp.currentInvestment - dwp.totalInvestment) AS totalPnL
    FROM MF_DayWisePosition dwp 
    JOIN USERS u ON dwp.userId = u.id 
    -- Filtering for the last 30 days of data
    WHERE dwp.asOfDate >= DATE('now', '-3000 days', 'localtime')
    GROUP BY dwp.asOfDate, u.username
)
SELECT 
    asOfDate,
    userName,
    totalInvested,
    currentVal,
    totalPnL AS cumulativePnL,
    -- Daily PnL Change (Today's PnL - Yesterday's PnL)
    ROUND(totalPnL - LAG(totalPnL) OVER (PARTITION BY userName ORDER BY asOfDate), 2) AS dailyChange,
    -- Daily Change %: (Daily Change / Total Invested) * 100
    ROUND(
        (totalPnL - LAG(totalPnL) OVER (PARTITION BY userName ORDER BY asOfDate)) * 100.0 / 
        NULLIF(currentVal, 0), 
    2) || '%' AS dailyChangePercent
FROM DailySnapshots
ORDER BY asOfDate DESC, userName;
