SELECT 
    t.transactionDate,
    u.username AS user_name,  -- Or u.name depending on your schema
    m.mutualFund AS mutual_fund_name,
    t.transactionType,
    t.amount,
    t.units,
    t.nav,
    t.totalAmount
FROM MF_INVESTMENTS_TRANSACTIONS t
JOIN USERS u ON t.userId = u.id
JOIN MF_MASTER m ON t.mutualFundId = m.id
ORDER BY t.transactionDate DESC;