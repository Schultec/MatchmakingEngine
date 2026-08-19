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
        self._total_players = 0

    def get_total_players(self):
        return self._total_players

    def add_to_queue(self, target) -> bool:

        if isinstance(target, Ticket):
            ticket = target
            player = ticket.player
        elif isinstance(target, Player):
            player = target
            ticket = Ticket(player=player, created_at=time.time())
        else:
            raise TypeError
        if player.id in self.player_to_bucket:
            return False

        bucket =  self.get_bucket_id(player.rating)
        region_name = player.region.name

        if bucket not in self.active_tickets[region_name]:
            self.active_tickets[region_name][bucket] = {}

        self.active_tickets[region_name][bucket][ticket.player.id] = ticket
        self.player_to_bucket[ticket.player.id] = bucket
        self._total_players += 1
        return True

    def remove_from_queue(self, player_id: str, player_region: str) -> bool:
        """
        :param player_id:
        :param player_region:
        """
        if player_id not in self.player_to_bucket:
            return False

        bucket_id =  self.player_to_bucket[player_id]

        if player_id in self.active_tickets[player_region][bucket_id]:
            del self.active_tickets[player_region][bucket_id][player_id]

        del self.player_to_bucket[player_id]
        self._total_players -= 1
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