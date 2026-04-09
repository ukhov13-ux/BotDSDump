import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class SignalManager:
    def __init__(self, db_pool, redis, telegram_queue):
        self.db = db_pool
        self.redis = redis
        self.telegram_queue = telegram_queue

    async def create_signal(self, coin_id, direction, price, meta):
        async with self.db.acquire() as conn:
            signal_id = await conn.fetchval("""
                INSERT INTO signals (coin_id, direction, entry_price, entry_time)
                VALUES ($1, $2, $3, NOW()) RETURNING id
            """, coin_id, direction, price)
        await self.telegram_queue.put({
            'type': 'signal',
            'id': signal_id,
            'coin_id': coin_id,
            'direction': direction,
            'price': price,
            **meta
        })
        return signal_id

    async def update_signal_result(self, signal_id, current_price):
        async with self.db.acquire() as conn:
            signal = await conn.fetchrow("SELECT * FROM signals WHERE id=$1", signal_id)
            if not signal:
                return
            change = (current_price - signal['entry_price']) / signal['entry_price']
            status = 'SUCCESS' if (signal['direction'] == 'PUMP' and change > 0) or (signal['direction'] == 'DUMP' and change < 0) else 'FAILED'
            await conn.execute("""
                UPDATE signals SET status=$1, exit_price=$2, exit_time=NOW(), change_pct=$3
                WHERE id=$4
            """, status, current_price, change * 100, signal_id)
