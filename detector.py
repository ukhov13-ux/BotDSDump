import logging
from config import *

logger = logging.getLogger(__name__)

class Detector:
    def __init__(self, db_pool, redis):
        self.db = db_pool
        self.redis = redis

    async def analyze(self, coin_id, exchange, symbol, data):
        change_1m = (data['current_price'] - data['price_1m_ago']) / data['price_1m_ago'] if data['price_1m_ago'] else 0
        change_5m = (data['current_price'] - data['price_5m_ago']) / data['price_5m_ago'] if data['price_5m_ago'] else 0
        taker_ratio = data['taker_buy_volume'] / data['taker_sell_volume'] if data['taker_sell_volume'] > 0 else 999
        vol_spike = data['volume_5m'] / data['avg_volume_5m'] if data['avg_volume_5m'] > 0 else 0

        if (change_1m >= PUMP_1M_PCT or change_5m >= PUMP_5M_PCT) \
                and taker_ratio >= PUMP_TAKER_BUY_RATIO \
                and vol_spike >= VOLUME_SPIKE_MULTIPLIER:
            return {'type': 'PUMP', 'change': max(change_1m, change_5m), 'taker_ratio': taker_ratio}

        if (change_1m <= DUMP_1M_PCT or change_5m <= DUMP_5M_PCT) \
                and (1/taker_ratio) >= DUMP_TAKER_SELL_RATIO \
                and vol_spike >= VOLUME_SPIKE_MULTIPLIER:
            return {'type': 'DUMP', 'change': min(change_1m, change_5m), 'taker_ratio': taker_ratio}

        return None
