import logging
from datetime import datetime, timedelta
from config import *

logger = logging.getLogger(__name__)

class GrowthMonitor:
    def __init__(self, db_pool, redis):
        self.db = db_pool
        self.redis = redis

    async def scan_all(self):
        async with self.db.acquire() as conn:
            coins = await conn.fetch("""
                SELECT c.id, c.exchange, c.symbol FROM coins c
                LEFT JOIN blocked_coins bc ON bc.coin_id = c.id AND bc.blocked_until > NOW()
                WHERE c.is_active = true AND bc.coin_id IS NULL
            """)
        for coin in coins:
            await self._analyze_coin(coin)

    async def _analyze_coin(self, coin):
        async with self.db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT timestamp, close FROM candles
                WHERE coin_id = $1 AND timestamp > NOW() - INTERVAL '48 hours'
                ORDER BY timestamp
            """, coin['id'])
            if len(rows) < 20:
                return
            prices = [r['close'] for r in rows]
            times = [r['timestamp'] for r in rows]
            best_growth = 0.0
            best_start = best_end = None
            window_sizes = [12, 24, 48, 96, 144, 288, 432]
            for w in window_sizes:
                if w > len(prices):
                    continue
                for i in range(len(prices) - w):
                    start_p = prices[i]
                    end_p = prices[i + w]
                    growth = (end_p - start_p) / start_p if start_p > 0 else 0
                    if growth > best_growth:
                        best_growth = growth
                        best_start = times[i]
                        best_end = times[i + w]
            if best_growth >= HIGH_GROWTH_THRESHOLD:
                priority = 2 if best_growth >= EXTREME_GROWTH_THRESHOLD else 1
                await conn.execute("""
                    INSERT INTO high_growth_coins (coin_id, growth_pct, growth_start, growth_end, priority, detected_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    ON CONFLICT (coin_id) DO UPDATE SET
                        growth_pct = EXCLUDED.growth_pct,
                        growth_start = EXCLUDED.growth_start,
                        growth_end = EXCLUDED.growth_end,
                        priority = EXCLUDED.priority,
                        detected_at = NOW(),
                        is_active = true
                """, coin['id'], best_growth * 100, best_start, best_end, priority)

    async def get_high_growth_coins(self):
        async with self.db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT c.exchange, c.symbol, h.growth_pct, h.growth_start, h.priority
                FROM high_growth_coins h
                JOIN coins c ON c.id = h.coin_id
                WHERE h.is_active = true
                ORDER BY h.priority DESC, h.detected_at DESC
            """)
        return rows
