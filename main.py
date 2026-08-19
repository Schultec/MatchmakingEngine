import asyncio
import random
import time

import uvicorn
from Dashboard import dashboard
from Engine.metrics import MetricsAggregator
from Engine.matchmaker import matchmaker_loop
from Engine.models import Player, Ticket
from Engine.queue_manager import QueueManager
from Engine.rating import EloEngine
from sim_state import SimState
async def player_spawner(active_queue, sim_state: SimState):
    """
    Simulates organic player traffic hitting a game server.
    Generates unique players on a skill bell curve and adds them to the queue.
    """
    player_counter = 1

    # Bell curve configurations
    AVERAGE_ELO = 1500.0
    SKILL_SPREAD = 200.0  # 68% of players will be between 1300 and 1700 Elo

    max_concurrent = 15000

    print("[SIMULATOR] Player spawner started...")

    while True:
        current_load = active_queue.get_total_players()

        if current_load < max_concurrent:
            batch = 150 if sim_state.is_peak else 30
            for i in range(batch) :
                # 1. Create a unique ID
                player_id = f"Player_{player_counter}"

                # 2. Generate a realistic skill rating using a Gaussian distribution
                generated_rating = round(random.gauss(AVERAGE_ELO, SKILL_SPREAD), 1)
                # 3. Instantiate the Player model
                new_player = Player(player_id=player_id, initial_rating=generated_rating, region=random.choice(list(Player.Region)))

                # 4. Ingest them into the shared queue instance
                success = active_queue.add_to_queue(new_player)

                if success:
                    player_counter += 1

        # 5. Sleep for a random interval (0.001 to 0.4 seconds) to mimic organic traffic
        random_sleep_duration = random.uniform(0.05, 0.1)
        await asyncio.sleep(random_sleep_duration)

async def match_simulation_worker(match_buffer: list, active_queue: QueueManager):
    print("[SIMULATOR] Match simulation worker started...")

    elo_engine = EloEngine()

    while True:
        current_time = time.time()

        for i in range(len(match_buffer) - 1,  -1, -1):
            team_a, team_b, match_start_time = match_buffer[i]
            match_duration = random.uniform(4.0, 8.0)
            if current_time - match_start_time >= match_duration:
                match_buffer.pop(i)

                expected_score_a = elo_engine.get_expected_score(
                    team_a.average_rating,
                    team_b.average_rating,
                )
                expected_score_b = 1.0 - team_a.average_rating
                a_won = random.random() < expected_score_a
                outcome_a, outcome_b = (1.0, 0.0) if a_won else (0.0, 1.0)

                for ticket in team_a.players:
                    ticket.player.rating = round(
                        elo_engine.update_ratings(ticket.player, expected_score_a, outcome_a),
                        1
                    )

                for ticket in team_b.players:
                    ticket.player.rating = round(
                        elo_engine.update_ratings(ticket.player, expected_score_b, outcome_b),
                        1
                    )

                for ticket in (team_a.players + team_b.players):
                    asyncio.create_task(staggered_requeue(ticket, active_queue))

        await asyncio.sleep(0.5)


async def staggered_requeue(ticket: Ticket, active_queue: QueueManager):
    await asyncio.sleep(random.uniform(1.0, 4.0))
    active_queue.add_to_queue(ticket.player)




async def run_simulation():
    # 1. Create the SINGLE shared instance of your waiting room
    sim_state = SimState()
    shared_server_queue = QueueManager()
    metrics = MetricsAggregator(sim_state)
    active_matches_buffer = []
    dashboard.app.state.metrics = metrics
    config = uvicorn.Config(dashboard.app, host="127.0.0.1", port=8000)
    server = uvicorn.Server(config)
    dashboard.app.state.sim_state = sim_state

    # 2. Tell Python to run the producer and consumer at the exact same time
    await asyncio.gather(
        player_spawner(shared_server_queue, sim_state),
        matchmaker_loop(shared_server_queue, metrics, active_matches_buffer),
        match_simulation_worker(active_matches_buffer, shared_server_queue),
        server.serve()
    )


if __name__ == "__main__":
    # Start the async runtime engine
    asyncio.run(run_simulation())