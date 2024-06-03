from app.elo import ELOMatch
from app.model import Game, Player, PlayerStatistics, Rating, User
from app.session import db


def find_or_create_user(telegram_id: int) -> User:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def create_rating_by_name(name: str, telegram_id: int) -> Rating | Exception:
    user = find_or_create_user(telegram_id)
    existing_rating = db.query(Rating).filter_by(user_id=user.id, name=name).first()
    if existing_rating:
        return Exception("rating already exist")

    rating = Rating(name=name, user_id=user.id)
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating


def get_user_ratings(telegram_id: int) -> list[Rating]:
    user = find_or_create_user(telegram_id=telegram_id)
    ratings = db.query(Rating).filter_by(user_id=user.id).all()
    return ratings


def delete_rating_by_id(rating_id: int) -> None | Exception:
    rating = db.query(Rating).filter_by(id=rating_id).first()
    if rating:
        db.delete(rating)
        db.commit()
        return
    return Exception("rating not found")


def get_rating_by_id(rating_id: int) -> Rating | Exception:
    rating = db.query(Rating).filter_by(id=rating_id).first()
    if rating:
        return rating
    return Exception("rating not found")


def create_rating_participant_by_name(
    rating_id: int, participant_name: str
) -> Player | Exception:
    rating = get_rating_by_id(rating_id)
    if isinstance(rating, Exception):
        return rating
    existing_participant = (
        db.query(Player).filter_by(rating_id=rating_id, name=participant_name).first()
    )

    if existing_participant:
        return Exception("participant already exist")

    return create_rating_participant(participant_name, rating_id)


def create_rating_participant(
    player_name: str,
    rating_id: int,
):
    new_statistics = PlayerStatistics()
    db.add(new_statistics)
    db.commit()
    new_participant = Player(
        name=player_name, rating_id=rating_id, statistics=new_statistics
    )
    db.add(new_participant)
    db.commit()
    return new_participant


def get_rating_participants(rating_id: int) -> list[Player]:
    rating = get_rating_by_id(rating_id)
    if isinstance(rating, Exception):
        return []
    return rating.players


def get_participant_statistics(participant_id: int) -> PlayerStatistics | Exception:
    participant = db.query(Player).filter_by(id=participant_id).first()
    if participant:
        return participant.statistics
    return Exception("participant not found")


def delete_rating_participant(rating_id: int, participant_id: int) -> None | Exception:
    rating = get_rating_by_id(rating_id)
    if isinstance(rating, Exception):
        return rating
    participant = db.query(Player).filter_by(id=participant_id).first()
    if participant:
        db.delete(participant)
        db.commit()
        return
    return Exception("participant not found")


def create_game_with_rankings(
    participant_leaderboard: dict[int, int], rating_id: int
) -> None:
    """Create a game and update Elo ratings based on ranks."""
    rating = get_rating_by_id(rating_id)
    if isinstance(rating, Exception):
        return rating

    elo_match = ELOMatch()

    for player_id, rank in participant_leaderboard.items():
        participant = get_participant_by_id(player_id)
        if isinstance(participant, Exception):
            continue
        elo_match.add_player(
            player_id=player_id, place=rank, elo=participant.statistics.rating_value
        )

    elo_match.calculate_elo()

    new_game = Game(rating_id=rating_id)
    db.add(new_game)
    db.commit()

    for player in elo_match.players:
        participant = get_participant_by_id(player.player_id)
        if isinstance(participant, Exception):
            continue
        participant.statistics.rating_value = player.elo_post
        participant.statistics.played_games += 1
        if player.place == 1:
            participant.statistics.wins += 1
        new_game.participants.append(participant)
        db.commit()


def get_participant_by_id(player_id: int) -> Player | Exception:
    participant = db.query(Player).filter_by(id=player_id).first()
    if participant:
        return participant
    return Exception("participant not found")


def get_metrics():
    # Count all users of the bot
    total_users = db.query(User).count()

    # Count all users with at least 1 created rating
    users_with_ratings = db.query(User).join(Rating).distinct().count()

    # Count number of all created ratings
    total_ratings = db.query(Rating).count()
    # Count number of all created games
    total_games = db.query(Game).count()

    return {
        "total_users": total_users,
        "users_with_ratings": users_with_ratings,
        "total_games": total_games,
        "total_ratings": total_ratings,
    }
