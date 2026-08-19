from Engine import models

class EloEngine:
    def __init__(self, k_factor: int = 32):
        self.k_factor = k_factor

    def get_expected_score(self, player_rating: float, opponent_rating: float) -> float:
        """
        :param player_rating:
        :param opponent_rating:
        :return expected_score:
        calculate the likelihood of a player winning a match
        """
        exponent = (opponent_rating - player_rating) / 400
        exponent = max(-12.0, min(12.0, exponent))
        dem = 1 + 10 ** exponent
        return 1 / dem

    def update_ratings(self, player_a: models.Player, expected_outcome: float, outcome: float):
        """
        :param player_a:
        :param expected_outcome:
        :param outcome:
        :return new_rating:
        calculate and update the rating of the player
        """
        return player_a.rating + (self.k_factor * (outcome - expected_outcome))