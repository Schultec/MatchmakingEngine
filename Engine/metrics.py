import time
import statistics
from Engine import models
from collections import deque
from itertools import product

class MetricsAggregator:
    def __init__(self, sim_state):
        self.match_history = deque(maxlen=500)
        self.queue_snapshots = {}
        self.match_count = 0
        self.start_time = time.time()
        self.sim_state = sim_state
        self.rivalry_counts = {}

    def record_match(self, region, team1: models.Team, team2: models.Team, curr):
        all_players = team1.players + team2.players
        avg_waittime = statistics.mean(curr - t.created_at for t in all_players)
        team1_ids = [t.player.id for t in team1.players]
        team2_ids = [t.player.id for t in team2.players]
        hottest_pair, hottest_count = None, 0
        for id_a, id_b in product(team1_ids, team2_ids):
            key  = tuple(sorted((id_a, id_b)))
            self.rivalry_counts[key] = self.rivalry_counts.get(key, 0) + 1
            if self.rivalry_counts[key] > hottest_count:
                hottest_pair, hottest_count = key, self.rivalry_counts[key]
        match_hist_entry = {
            "Region": region,
            "team1_players": [{"id": t.player.id, "rating": round(t.player.rating, 1)} for t in team1.players],
            "team2_players": [{"id": t.player.id, "rating": round(t.player.rating, 1)} for t in team2.players],
            "team1_rating": round(team1.average_rating, 1),
            "team2_rating": round(team2.average_rating, 1),
            "ELO_Diff": round(abs(team1.average_rating - team2.average_rating), 1),
            "avg_waittime": round(avg_waittime, 2),
            "timestamp": curr,
            "rivalry_pair": list(hottest_pair) if hottest_pair else None,
            "rivalry_count": hottest_count,
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
        top_rivalries = sorted(self.rivalry_counts.items(), key=lambda kv: -kv[1])[:10]
        return {
            "matches per second": self.match_count / (time.time() - self.start_time),
            "avg elo diff": result_elo,
            "avg waittime": result_waittime,
            "queue depth per region": self.queue_snapshots,
            "total matches": self.match_count,
            "recent matches": list(self.match_history)[-20:],
            "is_peak": self.sim_state.is_peak,
            "top rivalries": [{"players": list(pair), "meetings": count} for pair, count in top_rivalries]
        }