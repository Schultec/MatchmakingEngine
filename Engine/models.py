import time
import math
from enum import Enum


class Player:

    class Region(Enum):
        NA_East = 0
        NA_West = 1
        EU_West = 2
        EU_East = 3
        APAC = 4
        LATAM = 5
        AFRICA = 6

    def __init__(self, player_id: str,region: Region, initial_rating: float = 1500.0):
        self.id = player_id
        self.rating = initial_rating
        self.region = region

class Ticket:
    def __init__ (self, player: Player, created_at: float):
        self.player = player
        self.created_at = created_at

    @property
    def allowed_gap(self) -> float:
        curr = time.time()
        seconds_elapsed = curr - self.created_at
        exponent = (-0.3 * (seconds_elapsed-10))
        calculated_gap = 300/(1+math.e ** exponent)
        return calculated_gap