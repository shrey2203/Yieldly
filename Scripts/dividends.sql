SELECT 
    u.username AS "User Name",
    e.equityShortName AS "Ticker",
    e.equityLongName AS "Company Name",
    SUM(d.totalDividendAmount) AS "Total Dividends Received",
    COUNT(d.id) AS "Number of Payouts"
FROM DIVIDENDS_HISTORICAL d
JOIN USERS u ON d.userId = u.id
JOIN EQUITY_MASTER e ON d.equityId = e.id
GROUP BY u.username, e.equityShortName, e.equityLongName
ORDER BY "Total Dividends Received" DESC;