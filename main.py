import asyncio
import logging
from db import init_db, get_db_pool
from redisclient import get_redis
from filters import CoinFilter
from metrics import MetricsCalculator
from growth import GrowthMonitor
from priority import PriorityScanQueue
from stream import StreamProcessor
from signals import SignalManager
from telegrambot import run_telegram_bot
from config import SERVICE_MODE, EXCHANGES, GROWTH_SCAN_INTERVAL_MINUTES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    await init_db()
    db_pool = await get_db_pool()
    redis = await get_redis()
    telegram_queue = asyncio.Queue()

    growth_monitor = GrowthMonitor(db_pool, redis)
    priority_queue = PriorityScanQueue(growth_monitor)
    signal_manager = SignalManager(db_pool, redis, telegram_queue)
    stream_proc = StreamProcessor(db_pool, redis, signal_manager, priority_queue)

    asyncio.create_task(run_telegram_bot(telegram_queue))

    if SERVICE_MODE in ("all", "analyzer"):
        metrics_calc = MetricsCalculator(db_pool, redis)
        logger.info("Calculating initial metrics...")
        await metrics_calc.recalc_all_active()
        logger.info("Initial growth scan...")
        await growth_monitor.scan_all()

        async def growth_loop():
            while True:
                await asyncio.sleep(GROWTH_SCAN_INTERVAL_MINUTES * 60)
                await growth_monitor.scan_all()
                all_symbols = []
                await priority_queue.refresh(all_symbols)

        asyncio.create_task(growth_loop())

    if SERVICE_MODE in ("all", "websocket"):
        await stream_proc.run()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
