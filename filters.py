import logging
import ccxt.async_support as ccxt
from config import *

logger = logging.getLogger(__name__)

class CoinFilter:
    def __init__(self, exchange_id, db_pool, redis):
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)({'enableRateLimit': True})
        self.db = db_pool
        self.redis = redis

    async def load_markets(self):
        return await self.exchange.load_markets()

    async def get_filtered_symbols(self):
        markets = await self.load_markets()
        valid = []
        for symbol, market in markets.items():
            if market.get('type') != 'spot' or market.get('quote') != 'USDT':
                continue
            if not await self._check_basic(symbol):
                continue
            valid.append(symbol)
        return valid

    async def _check_basic(self, symbol):
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
        except:
            return False
        if ticker.get('quoteVolume', 0) < MIN_24H_VOLUME_USD.get(self.exchange_id, 350_000):
            return False
        bid, ask = ticker.get('bid'), ticker.get('ask')
        if bid and ask and bid > 0:
            if (ask - bid) / bid * 100 > MAX_SPREAD_PCT:
                return False
        try:
            ob = await self.exchange.fetch_order_book(symbol, limit=50)
            if len(ob['bids']) < MIN_ORDERBOOK_DEPTH_ORDERS or len(ob['asks']) < MIN_ORDERBOOK_DEPTH_ORDERS:
                return False
        except:
            return False
        async with self.db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 1 FROM blocked_coins bc
                JOIN coins c ON c.id = bc.coin_id
                WHERE c.exchange=$1 AND c.symbol=$2 AND bc.blocked_until > NOW()
            """, self.exchange_id, symbol)
            if row:
                return False
        return True

    async def update_coin_in_db(self, symbol, market_cap=None):
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO coins (exchange, symbol, base, quote, market_cap)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (exchange, symbol) DO UPDATE SET market_cap=$5, is_active=true
            """, self.exchange_id, symbol, symbol.split('/')[0], symbol.split('/')[1], market_cap)
