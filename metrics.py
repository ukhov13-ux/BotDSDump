import logging
import asyncio
import numpy as np
from exchange import create_exchange, fetch_ohlcv
from config import *

logger = logging.getLogger(__name__)

class MetricsCalculator:
    def __init__(self, db_pool, redis):
        self.db = db_pool
        self.redis = redis

    async def update_metrics_for_coin(self, coin_id, exchange, symbol):
        ex = create_exchange(exchange)
        candles = await fetch_ohlcv(ex, symbol, '5m', limit=2000)
        if not candles:
            return
        async with self.db.acquire() as conn:
            for c in candles:
                await conn.execute("""
                    INSERT INTO candles (coin_id, timestamp, open, high, low, close, volume, buy_volume, sell_volume)
                    VALUES ($1, to_timestamp($2/1000), $3, $4, $5, $6, $7, 0, 0)
                    ON CONFLICT DO NOTHING
                """, coin_id, c[0], c[1], c[2], c[3], c[4], c[5])
        recent = candles[-576:]
        if not recent:
            return
        closes = [c[4] for c in recent]
        volumes = [c[5] for c in recent]
        avg_volume_5m = np.mean(volumes) if volumes else 0
        volatility = np.std(closes) / np.mean(closes) if closes else 0
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO metrics_cache (coin_id, avg_volume_5m, volatility_1h, updated_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (coin_id) DO UPDATE SET
                    avg_volume_5m = EXCLUDED.avg_volume_5m,
                    volatility_1h = EXCLUDED.volatility_1h,
                    updated_at = NOW()
            """, coin_id, avg_volume_5m, volatility)

    async def recalc_all_active(self):
        async with self.db.acquire() as conn:
            coins = await conn.fetch("SELECT id, exchange, symbol FROM coins WHERE is_active=true")
        for coin in coins:
            await self.update_metrics_for_coin(coin['id'], coin['exchange'], coin['symbol'])
            await asyncio.sleep(0.5)
