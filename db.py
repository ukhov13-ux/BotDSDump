import asyncpg
import logging
from config import DATABASE_URL

logger = logging.getLogger(__name__)

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS coins (
                id SERIAL PRIMARY KEY,
                exchange TEXT NOT NULL,
                symbol TEXT NOT NULL,
                base TEXT,
                quote TEXT,
                market_cap DOUBLE PRECISION,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(exchange, symbol)
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS candles (
                coin_id INT REFERENCES coins(id) ON DELETE CASCADE,
                timestamp TIMESTAMPTZ NOT NULL,
                open DOUBLE PRECISION,
                high DOUBLE PRECISION,
                low DOUBLE PRECISION,
                close DOUBLE PRECISION,
                volume DOUBLE PRECISION,
                buy_volume DOUBLE PRECISION,
                sell_volume DOUBLE PRECISION,
                trades INT,
                PRIMARY KEY (coin_id, timestamp)
            )
        ''')
        await conn.execute('CREATE EXTENSION IF NOT EXISTS timescaledb')
        await conn.execute("SELECT create_hypertable('candles', 'timestamp', if_not_exists => TRUE)")
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                coin_id INT REFERENCES coins(id),
                direction TEXT NOT NULL,
                entry_price DOUBLE PRECISION,
                entry_time TIMESTAMPTZ DEFAULT NOW(),
                status TEXT DEFAULT 'PENDING',
                exit_price DOUBLE PRECISION,
                exit_time TIMESTAMPTZ,
                change_pct DOUBLE PRECISION,
                checked_1h BOOLEAN DEFAULT FALSE,
                checked_4h BOOLEAN DEFAULT FALSE
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS blocked_coins (
                coin_id INT REFERENCES coins(id) PRIMARY KEY,
                blocked_until TIMESTAMPTZ NOT NULL,
                reason TEXT
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS metrics_cache (
                coin_id INT REFERENCES coins(id) PRIMARY KEY,
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                avg_volume_5m DOUBLE PRECISION,
                avg_volume_1h DOUBLE PRECISION,
                volatility_1h DOUBLE PRECISION,
                avg_spread DOUBLE PRECISION,
                taker_ratio_avg DOUBLE PRECISION
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS high_growth_coins (
                id SERIAL PRIMARY KEY,
                coin_id INT REFERENCES coins(id) ON DELETE CASCADE,
                detected_at TIMESTAMPTZ DEFAULT NOW(),
                growth_pct DOUBLE PRECISION,
                growth_start TIMESTAMPTZ,
                growth_end TIMESTAMPTZ,
                priority INT DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_high_growth_active ON high_growth_coins(is_active, priority DESC)')
        logger.info("Database initialized")
    finally:
        await conn.close()

async def get_db_pool():
    return await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
