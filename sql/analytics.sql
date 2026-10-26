SELECT
    symbol,
    COUNT(*) AS total_rows,
    MIN(trading_date) AS first_date,
    MAX(trading_date) AS last_date,
    ROUND(AVG(close), 2) AS avg_close,
    MIN(close) AS min_close,
    MAX(close) AS max_close,
    SUM(volume) AS total_volume
FROM stock_prices
GROUP BY symbol
ORDER BY symbol;