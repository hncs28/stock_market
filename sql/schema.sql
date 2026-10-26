CREATE TABLE IF NOT EXISTS stock_prices (
    symbol VARCHAR(10) NOT NULL,
    trading_date DATE NOT NULL,

    open NUMERIC(14, 2) NOT NULL,
    high NUMERIC(14, 2) NOT NULL,
    low NUMERIC(14, 2) NOT NULL,
    close NUMERIC(14, 2) NOT NULL,

    volume BIGINT NOT NULL,

    source VARCHAR(20) NOT NULL DEFAULT 'vci',
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_stock_prices
        PRIMARY KEY (symbol, trading_date),

    CONSTRAINT chk_prices_non_negative
        CHECK (
            open >= 0
            AND high >= 0
            AND low >= 0
            AND close >= 0
            AND volume >= 0
        ),

    CONSTRAINT chk_high_low
        CHECK (high >= low)
);