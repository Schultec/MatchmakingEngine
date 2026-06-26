import asyncio
from Engine.metrics import MetricsAggregator
import time


async def matchmaker_loop(active_queue, metrics: MetricsAggregator):
    print("[MATCHMAKER] Initializing systems...")
    await asyncio.sleep(1)
    regions = ["NA_East", "NA_West", "EU_West", "EU_East", "APAC", "LATAM", "AFRICA"]
    while True:
        curr = time.time()

        for region in regions:
            queue = active_queue.get_active_tickets(region)
            depth = sum(len(bucket) for bucket in queue.values())
            metrics.record_snapshot(region, depth)
            matched_ids = set()
            for bucket in queue.values():
                for ticket in sorted(list(bucket.values()), key=lambda t: t.created_at):
                    if ticket.player.id in matched_ids:
                        continue
                    tickets_to_remove = []
                    min_bucket = active_queue.get_bucket_id(ticket.player.rating - ticket.allowed_gap)
                    max_bucket = active_queue.get_bucket_id(ticket.player.rating + ticket.allowed_gap)
                    match_found = False
                    for target_bucket_id in range(min_bucket, max_bucket + 1):
                        if target_bucket_id in queue:
                            target_bucket = queue[target_bucket_id]
                            for ticket2 in sorted(list(target_bucket.values()), key=lambda t: t.created_at):
                                if ticket.player.id == ticket2.player.id or ticket2.player.id in matched_ids:
                                    continue
                                diff = abs(ticket.player.rating - ticket2.player.rating)
                                if diff <= ticket.allowed_gap and diff <= ticket2.allowed_gap:
                                    matched_ids.add(ticket.player.id)
                                    matched_ids.add(ticket2.player.id)
                                    tickets_to_remove.append(ticket)
                                    tickets_to_remove.append(ticket2)
                                    match_found = True
                                    metrics.record_match(region, ticket, ticket2, curr)
                        if match_found:
                            for item in tickets_to_remove:
                                active_queue.remove_from_queue(item.player.id, item.player.region.name)
                            break
        await asyncio.sleep(1)