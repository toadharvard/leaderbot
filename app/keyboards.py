from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from app.usecase import get_participant_by_id, get_rating_participants

CHECK_MARK = "✅"
CROSS_MARK = "❌"


def start_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Rating", callback_data="load_rating")
    return keyboard.as_markup()


def rating_menu_keyboard(rating_id):
    keyboard = InlineKeyboardBuilder()
    participants = get_rating_participants(rating_id)
    for participant in participants:
        keyboard.row(
            InlineKeyboardButton(
                text=participant.name,
                callback_data=f"show_participant_statistics_{participant.id}",
            ),
            width=1,
        )

    keyboard.row(
        InlineKeyboardButton(text="New Participant", callback_data="add_participant"),
        InlineKeyboardButton(text="New Game", callback_data="add_game"),
        InlineKeyboardButton(text="Delete Rating", callback_data="delete_rating"),
        InlineKeyboardButton(text="Start Menu", callback_data="return_to_start"),
        InlineKeyboardButton(text="Statistics", callback_data="show_rating_statistics"),
        width=2,
    )

    return keyboard.as_markup()


def return_to_start_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Return to Start", callback_data="return_to_start")
    return keyboard.as_markup()


def return_to_rating_menu_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Menu", callback_data="return_to_rating_menu")
    return keyboard.as_markup()


def player_profile_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="Delete Player", callback_data="delete_participant"),
        InlineKeyboardButton(text="Back", callback_data="return_to_rating_menu"),
        width=1,
    )
    return keyboard.as_markup()


def select_players_keyboard(game_participant_selection):
    keyboard = InlineKeyboardBuilder()
    for participant_id, selected in game_participant_selection.items():
        participant = get_participant_by_id(participant_id)
        keyboard.row(
            InlineKeyboardButton(
                text=f"{CHECK_MARK if selected else CROSS_MARK}    {participant.name}",
                callback_data=f"select_player_{participant.id}",
            ),
            width=1,
        )
    keyboard.row(
        InlineKeyboardButton(text="Start Ranking", callback_data="start_ranking"),
        width=1,
    )
    keyboard.row(
        InlineKeyboardButton(text="Menu", callback_data="return_to_rating_menu"),
        width=1,
    )
    return keyboard.as_markup()


def create_new_rating_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Create Rating", callback_data="create_rating")
    return keyboard.as_markup()


def rank_to_emoji(rank):
    return "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else rank


def assign_rank_keyboard(participant_leaderboard):
    keyboard = InlineKeyboardBuilder()
    for participant_id, rank in participant_leaderboard.items():
        participant = get_participant_by_id(participant_id)
        keyboard.row(
            InlineKeyboardButton(
                text=f"{participant.name} — {rank_to_emoji(rank) if rank is not None else 'N/A'}",
                callback_data=f"rank_{participant_id}",
            ),
            width=1,
        )

    if all(value is not None for value in participant_leaderboard.values()):
        keyboard.row(
            InlineKeyboardButton(text="Finish", callback_data="finish_ranking"), width=1
        )
    keyboard.row(
        InlineKeyboardButton(text="Menu", callback_data="return_to_rating_menu"),
        width=1,
    )
    return keyboard.as_markup()


def load_rating_keyboard(ratings):
    keyboard = InlineKeyboardBuilder()
    for rating in ratings:
        keyboard.row(
            InlineKeyboardButton(
                text=rating.name, callback_data=f"select_rating_{rating.id}"
            ),
            width=1,
        )
    keyboard.row(
        InlineKeyboardButton(text="Return to Start", callback_data="return_to_start"),
        InlineKeyboardButton(text="Create New Rating", callback_data="create_rating"),
        width=1,
    )
    return keyboard.as_markup()


def rank_game_participant_keyboard(
    participant_leaderboard: dict[int, int], game_participant_id: int
):
    keyboard = InlineKeyboardBuilder()
    for i in range(1, len(participant_leaderboard) + 1):
        keyboard.row(
            InlineKeyboardButton(
                text=str(rank_to_emoji(i)),
                callback_data=f"assign_rank_{game_participant_id}_{i}",
            ),
            width=1,
        )
    return keyboard.as_markup()
