import logging

logger = logging.getLogger(__name__)

class PriorityScanQueue:
    def __init__(self, growth_monitor):
        self.gm = growth_monitor
        self.high_priority = set()
        self.normal = set()

    async def refresh(self, all_coins):
        high = await self.gm.get_high_growth_coins()
        self.high_priority = {f"{c['exchange']}:{c['symbol']}" for c in high}
        self.normal = set(all_coins) - self.high_priority

    def get_scan_order(self):
        return list(self.high_priority) + list(self.normal)
