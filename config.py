import os
from dotenv import load_dotenv

load_dotenv()

# Биржи
EXCHANGES = ['binance', 'bybit', 'okx', 'kucoin', 'htx']
EXCHANGE_PRIORITY = ['binance', 'bybit', 'okx', 'kucoin', 'htx']

# Фильтры
EXCLUDE_TOP_N = 30
MIN_DAYS_SINCE_LISTING = 3
MAX_SPREAD_PCT = 0.4
MIN_ORDERBOOK_DEPTH_ORDERS = 25

MIN_24H_VOLUME_USD = {
    'binance': 500_000,
    'bybit': 500_000,
    'okx': 350_000,
    'kucoin': 350_000,
    'htx': 350_000,
}
MIN_MARKET_CAP = {
    'binance': 10_000_000,
    'bybit': 5_000_000,
    'okx': 1_000_000,
    'kucoin': 1_000_000,
    'htx': 1_000_000,
}
MIN_TRADES_24H = 1500
MIN_HOURLY_VOLUME = 10_000

# Антинакрутка
WASH_TRADE_THRESHOLD_PCT = 0.3
WASH_TRADE_ADDRESSES = 10
BLOCK_HOURS = 36

# Детекция
PUMP_1M_PCT = 0.03
PUMP_5M_PCT = 0.07
PUMP_TAKER_BUY_RATIO = 1.8

DUMP_1M_PCT = -0.02
DUMP_5M_PCT = -0.05
DUMP_TAKER_SELL_RATIO = 2.0

VOLUME_SPIKE_MULTIPLIER = 4.0
MIN_LARGE_TRADE_USD = 10_000

REVERSAL_PRICE_MOVE_PCT = 0.02
REVERSAL_TAKER_RATIO = 1.5

# Рост
GROWTH_SCAN_INTERVAL_MINUTES = 5
HIGH_GROWTH_THRESHOLD = 0.30
EXTREME_GROWTH_THRESHOLD = 0.60
GROWTH_LOOKBACK_HOURS = 48

# Переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
SERVICE_MODE = os.getenv("SERVICE_MODE", "all")
