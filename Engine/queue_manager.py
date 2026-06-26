import time
from Engine.models import Player, Ticket

class QueueManager:
    def __init__(self):
        self.active_tickets = {
            "NA_East":{},
            "NA_West":{},
            "EU_West":{},
            "EU_East":{},
            "APAC":{},
            "LATAM":{},
            "AFRICA":{}
        }
        self.player_to_bucket = {}
        self.bucket_width = 100

    def add_to_queue(self, player: Player) -> bool:
        """
        :param player:
        """
        if player.id in self.player_to_bucket:
            return False
        bucket = self.get_bucket_id(player.rating)
        ticket = Ticket(player=player, created_at=time.time())
        if bucket in self.active_tickets[player.region.name]:
            self.active_tickets[player.region.name][bucket][player.id] = ticket
            self.player_to_bucket[player.id] = bucket
            return True
        else:
            self.active_tickets[player.region.name][bucket] = {player.id: ticket}
            self.player_to_bucket[player.id] = bucket
            return True

    def remove_from_queue(self, player_id: str, player_region: str) -> bool:
        """
        :param player_id:
        :param player_region:
        """
        if player_id not in self.player_to_bucket:
            return False
        del self.active_tickets[player_region][self.player_to_bucket[player_id]][player_id]
        del self.player_to_bucket[player_id]
        return True

    def get_active_tickets(self, region: str) -> dict[int,dict[str, Ticket]]:
        """
        :param region:
        """
        return self.active_tickets[region]

    def get_bucket_id(self, rating: float):
        """
        :param rating:
        """
        return int(rating // self.bucket_width)