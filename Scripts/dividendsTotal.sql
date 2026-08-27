SELECT    
    u.username, 
    SUM(d.totalDividendAmount) AS "Total Dividends Received"
FROM DIVIDENDS_HISTORICAL d
JOIN USERS u ON d.userId = u.id
GROUP BY u.id, u.username, u.emailAddress
ORDER BY "Total Dividends Received" DESC;