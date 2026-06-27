import asyncio
import random
import uvicorn
from Dashboard import dashboard
from Engine.metrics import MetricsAggregator
from Engine.matchmaker import matchmaker_loop
from Engine.models import Player
from Engine.queue_manager import QueueManager


async def player_spawner(active_queue):
    """
    Simulates organic player traffic hitting a game server.
    Generates unique players on a skill bell curve and adds them to the queue.
    """
    player_counter = 1

    # Bell curve configurations
    AVERAGE_ELO = 1500.0
    SKILL_SPREAD = 200.0  # 68% of players will be between 1300 and 1700 Elo

    print("[SIMULATOR] Player spawner started...")

    while True:
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
        random_sleep_duration = random.uniform(0.001, 0.4)
        await asyncio.sleep(random_sleep_duration)


async def run_simulation():
    # 1. Create the SINGLE shared instance of your waiting room
    shared_server_queue = QueueManager()
    metrics = MetricsAggregator()
    dashboard.app.state.metrics = metrics
    config = uvicorn.Config(dashboard.app, host="127.0.0.1", port=8000)
    server = uvicorn.Server(config)

    # 2. Tell Python to run the producer and consumer at the exact same time
    await asyncio.gather(
        player_spawner(shared_server_queue),
        matchmaker_loop(shared_server_queue, metrics),
        server.serve()
    )


if __name__ == "__main__":
    # Start the async runtime engine
    asyncio.run(run_simulation())