import time
import statistics
from Engine import models
from collections import deque

class MetricsAggregator:
    def __init__(self):
        self.match_history = deque(maxlen=500)
        self.queue_snapshots = {}
        self.match_count = 0
        self.start_time = time.time()

    def record_match(self, region, ticket1: models.Ticket, ticket2: models.Ticket, curr):
        match_hist_entry = {
            "Region": region,
            "player1": ticket1.player.id,
            "player2": ticket2.player.id,
            "player1_rating": ticket1.player.rating,
            "player2_rating": ticket2.player.rating,
            "ELO_Diff": abs(ticket1.player.rating - ticket2.player.rating),
            "player1_waittime": curr - ticket1.created_at,
            "player2_waittime": curr - ticket2.created_at,
            "timestamp": curr,
        }
        self.match_history.append(match_hist_entry)
        self.match_count += 1

    def record_snapshot(self, region: str, depth: int):
        self.queue_snapshots[region] = depth

    def get_stats(self):
        data_elo = []
        data_waittime = []
        for match in self.match_history:
            data_elo.append(match["ELO_Diff"])
            data_waittime.append(match["player1_waittime"])
            data_waittime.append(match["player2_waittime"])

        if not self.match_history:
            result_elo = 0
            result_waittime = 0

        result_elo = statistics.mean(data_elo)
        result_waittime = statistics.mean(data_waittime)

        return {
            "matches per second": self.match_count/(time.time() - self.start_time),
            "avg elo diff": result_elo,
            "avg waittime": result_waittime,
            "queue depth per region": self.queue_snapshots,
            "total matches": self.match_count,
            "recent matches": list(self.match_history)[-20:]
        }