import math


class ELOPlayer:
    def __init__(self, player_id: int, place: int, elo: float):
        self.player_id = player_id
        self.place = place
        self.elo_pre = elo
        self.elo_post = 0
        self.elo_change = 0


class ELOMatch:
    def __init__(self):
        self.players = []

    def add_player(self, player_id: int, place: int, elo: float):
        player = ELOPlayer(player_id, place, elo)
        self.players.append(player)

    def calculate_elo(self):
        n = len(self.players)
        K = 32 / (n - 1)
        for player in self.players:
            cur_place = player.place
            cur_elo = player.elo_pre

            for opponent in self.players:
                if player == opponent:
                    continue

                opponent_place = opponent.place
                opponent_elo = opponent.elo_pre

                if cur_place < opponent_place:
                    S = 1.0
                elif cur_place == opponent_place:
                    S = 0.5
                else:
                    S = 0.0

                EA = 1 / (1 + math.pow(10, (opponent_elo - cur_elo) / 400))
                player.elo_change += round(K * (S - EA))

            player.elo_post = player.elo_pre + player.elo_change
