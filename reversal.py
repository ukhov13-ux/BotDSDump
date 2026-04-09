import logging
from config import *

logger = logging.getLogger(__name__)

class ReversalMonitor:
    def __init__(self, db_pool, redis):
        self.db = db_pool
        self.redis = redis

    async def check_reversal(self, signal_id, current_price, current_taker_ratio):
        async with self.db.acquire() as conn:
            signal = await conn.fetchrow("""
                SELECT direction, entry_price FROM signals WHERE id=$1
            """, signal_id)
            if not signal:
                return None
            direction = signal['direction']
            entry = signal['entry_price']
            if direction == 'PUMP':
                high_key = f"signal:{signal_id}:high"
                high = await self.redis.get(high_key)
                if high:
                    high = float(high)
                    if current_price > high:
                        await self.redis.set(high_key, current_price)
                        return None
                else:
                    await self.redis.set(high_key, current_price)
                    return None
                drop = (high - current_price) / high
                if drop >= REVERSAL_PRICE_MOVE_PCT and (1/current_taker_ratio) >= REVERSAL_TAKER_RATIO:
                    return {'type': 'REVERSAL_DOWN', 'change': -drop}
            elif direction == 'DUMP':
                low_key = f"signal:{signal_id}:low"
                low = await self.redis.get(low_key)
                if low:
                    low = float(low)
                    if current_price < low:
                        await self.redis.set(low_key, current_price)
                        return None
                else:
                    await self.redis.set(low_key, current_price)
                    return None
                rise = (current_price - low) / low
                if rise >= REVERSAL_PRICE_MOVE_PCT and current_taker_ratio >= REVERSAL_TAKER_RATIO:
                    return {'type': 'REVERSAL_UP', 'change': rise}
        return None
