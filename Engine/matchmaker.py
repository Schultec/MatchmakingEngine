import asyncio
from Engine.metrics import MetricsAggregator
from Engine.models import Team
import time


async def matchmaker_loop(active_queue, metrics: MetricsAggregator, active_matches_buffer: list):
    print("[MATCHMAKER] Initializing systems...")
    await asyncio.sleep(1)
    regions = ["NA_East", "NA_West", "EU_West", "EU_East", "APAC", "LATAM", "AFRICA"]
    geo_topology = {
        "NA_East": {"NA_West": 1, "LATAM": 2, "EU_West": 3},
        "NA_West": {"NA_East": 1, "APAC": 2,  "LATAM": 2},
        "EU_West": {"EU_East": 1, "NA_East": 3, "AFRICA": 2},
        "EU_East": {"EU_West": 1, "APAC": 2,  "AFRICA": 2},
        "APAC": {"NA_West": 2, "EU_East": 2},
        "LATAM": {"NA_East": 2, "NA_West": 2},
        "AFRICA": {"EU_West": 2, "EU_East": 2}
    }
    while True:
        curr = time.time()

        claimed_this_tick = set()

        for region in regions:
            teams = []
            queue = active_queue.get_active_tickets(region)
            depth = sum(len(bucket) for bucket in queue.values())
            metrics.record_snapshot(region, depth)
            matched_ids = claimed_this_tick
            for bucket in queue.values():
                for ticket in sorted(list(bucket.values()), key=lambda t: t.created_at):
                    if ticket.player.id in matched_ids:
                        continue
                    teammates = []
                    wait_time = curr - ticket.created_at
                    search_regions = [region]
                    if wait_time >= 4.0:
                        search_regions.extend([r for r, tier in geo_topology[region].items() if tier == 1 ])
                    if wait_time >= 8.0:
                        search_regions.extend([r for r, tier in geo_topology[region].items() if tier == 2])
                    min_bucket = active_queue.get_bucket_id(ticket.player.rating - ticket.allowed_gap)
                    max_bucket = active_queue.get_bucket_id(ticket.player.rating + ticket.allowed_gap)
                    for target_bucket_id in range(min_bucket, max_bucket + 1):
                        for target_region in search_regions:
                            regional_queue = active_queue.get_active_tickets(target_region)
                            if target_bucket_id in regional_queue:
                                target_bucket = regional_queue[target_bucket_id]
                                for ticket2 in sorted(list(target_bucket.values()), key=lambda t: t.created_at):
                                    if ticket.player.id == ticket2.player.id or ticket2.player.id in matched_ids:
                                        continue
                                    diff = abs(ticket.player.rating - ticket2.player.rating)
                                    if diff <= ticket.allowed_gap and diff <= ticket2.allowed_gap:
                                        matched_ids.add(ticket2.player.id)
                                        teammates.append(ticket2)
                    if len(teammates) >= 4:
                        teams.append(Team([ticket] + teammates[:4]))
                        matched_ids.add(ticket.player.id)
                        break
            matched_teams = set()
            sorted_teams = sorted(teams, key=lambda t: t.average_rating)
            for i, team in enumerate(sorted_teams):
                if team in matched_teams:
                    continue
                for opponent in sorted_teams[i+1:]:
                    if opponent in matched_teams or opponent is team:
                        continue
                    diff = abs(team.average_rating - opponent.average_rating)
                    if diff > team.allowed_gap:
                        break
                    if diff <= team.allowed_gap and diff <= opponent.allowed_gap:
                        matched_teams.add(team)
                        matched_teams.add(opponent)
                        metrics.record_match(region, team, opponent, curr)

                        active_matches_buffer.append((team, opponent, time.time()))
                        for t in team.players + opponent.players:
                            active_queue.remove_from_queue(t.player.id, t.player.region.name)
                        break


        await asyncio.sleep(1)