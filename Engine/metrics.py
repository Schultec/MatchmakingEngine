import time
import statistics
from Engine import models
from collections import deque

class MetricsAggregator:
    def __init__(self, sim_state):
        self.match_history = deque(maxlen=500)
        self.queue_snapshots = {}
        self.match_count = 0
        self.start_time = time.time()
        self.sim_state = sim_state

    def record_match(self, region, team1: models.Team, team2: models.Team, curr):
        all_players = team1.players + team2.players
        avg_waittime = statistics.mean(curr - t.created_at for t in all_players)
        match_hist_entry = {
            "Region": region,
            "team1_players": [t.player.id for t in team1.players],
            "team2_players": [t.player.id for t in team2.players],
            "team1_rating": round(team1.average_rating, 1),
            "team2_rating": round(team2.average_rating, 1),
            "ELO_Diff": round(abs(team1.average_rating - team2.average_rating), 1),
            "avg_waittime": round(avg_waittime, 2),
            "timestamp": curr
        }
        self.match_history.append(match_hist_entry)
        self.match_count += 1

    def record_snapshot(self, region: str, depth: int):
        self.queue_snapshots[region] = depth

    def get_stats(self):
        if not self.match_history:
            result_elo = 0
            result_waittime = 0
        else:
            result_elo = statistics.mean(m["ELO_Diff"] for m in self.match_history)
            result_waittime = statistics.mean(m["avg_waittime"] for m in self.match_history)

        return {
            "matches per second": self.match_count / (time.time() - self.start_time),
            "avg elo diff": result_elo,
            "avg waittime": result_waittime,
            "queue depth per region": self.queue_snapshots,
            "total matches": self.match_count,
            "recent matches": list(self.match_history)[-20:],
            "is_peak": self.sim_state.is_peak
        }