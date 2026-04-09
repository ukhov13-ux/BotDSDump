import ccxt.asyncio_support as ccxt
import logging

logger = logging.getLogger(__name__)

def create_exchange(exchange_id: str):
    exchange_class = getattr(ccxt, exchange_id)
    return exchange_class({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})

async def fetch_ohlcv(exchange, symbol, timeframe='5m', limit=500):
    try:
        return await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching OHLCV {exchange.id} {symbol}: {e}")
        return []
