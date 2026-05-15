from src.fishbot.utils.logger import log


class StatsTracker:
    def __init__(self):
        self.stats = {
            'cycles': 0,
            'fish_caught': 0,
            'fish_escaped': 0,
            'rod_breaks': 0,
            'timeouts': 0
        }

    def increment(self, stat_name, value=1):
        if stat_name in self.stats:
            self.stats[stat_name] += value

    def show(self):
        log("")
        log("=" * 50)
        log("📊 STATISTICS")
        log("=" * 50)
        for stat, value in self.stats.items():
            title = stat.replace('_', ' ').replace('cycles', 'Cycles completed').capitalize()
            log(f"  {title}: {value}")
        log("=" * 50)
