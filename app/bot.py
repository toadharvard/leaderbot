import logging
from aiogram import F, Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

from app.filters import UserIDFilter
from app.session import init_db
from app.usecase import *
from app.keyboards import *

token = ""
logging.basicConfig(level=logging.INFO)
bot = Bot(token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class RatingStates(StatesGroup):
    start = State()
    new_rating = State()
    load_rating = State()
    delete_rating = State()
    rating_menu = State()
    add_participant = State()
    add_game = State()
    select_players = State()
    assign_ranks = State()


# Handlers
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    find_or_create_user(message.from_user.id)
    await state.set_state(RatingStates.start)
    await message.answer(
        "Welcome to the Bot! This bot allows you to create, manage, and play ratings. It has the following main functions:\n\n"
        "1. Create a new rating: This allows you to create a new rating system. You can give it a unique name and add participants to the rating.\n\n"
        "2. Load an existing rating: If you have created a rating before, you can load it and start managing it further.\n\n"
        "3. Play a game: If you have a rating with at least two participants, you can start a game to assign ranks to the participants.\n\n"
        "To get started, please choose an option below:",
        reply_markup=start_keyboard(),
    )


@dp.message(Command("kpi"), UserIDFilter(1752687551))
async def cmd_kpi(message: Message, state: FSMContext):
    metrics = get_metrics()
    metrics_str = "\n".join([f"{name}: {value}" for name, value in metrics.items()])
    await message.answer(f"All metrics:\n{metrics_str}")


@dp.callback_query(F.data == "create_rating")
async def create_rating(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RatingStates.new_rating)
    await callback.message.edit_text(
        "Please enter a name for the new rating:",
        reply_markup=return_to_start_keyboard(),
    )


@dp.message(RatingStates.new_rating, F.text)
async def receive_new_rating_name(message: Message, state: FSMContext):
    rating_name = message.text
    rating = create_rating_by_name(rating_name, message.from_user.id)
    if isinstance(rating, Exception):
        await message.answer(
            f"Rating '{rating_name}' already exists. Please use a different name."
        )
        return

    await state.update_data(rating_id=rating.id)
    await message.answer(
        f"Rating '{rating_name}' created successfully!",
        reply_markup=rating_menu_keyboard(rating.id),
    )
    await state.set_state(RatingStates.rating_menu)


@dp.callback_query(F.data == "load_rating")
async def load_rating(callback: CallbackQuery, state: FSMContext):
    ratings = get_user_ratings(callback.from_user.id)
    if not ratings:
        await callback.message.edit_text(
            "No ratings found. Please create one first.",
            reply_markup=create_new_rating_keyboard(),
        )
        return

    await state.set_state(RatingStates.load_rating)
    await callback.message.edit_text(
        "Select a rating:",
        reply_markup=load_rating_keyboard(ratings),
    )


@dp.callback_query(F.data == "delete_rating")
async def delete_rating(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    rating_id = data.get("rating_id")
    exc = delete_rating_by_id(rating_id)
    if isinstance(exc, Exception):
        await callback.message.edit_text(
            "Rating not found. Select options:", reply_markup=rating_menu_keyboard()
        )
        return
    await callback.message.edit_text(
        "Rating deleted successfully. Select options:", reply_markup=start_keyboard()
    )


@dp.callback_query(F.data.startswith("select_rating_"))
async def select_rating(callback: CallbackQuery, state: FSMContext):
    rating_id = int(callback.data.split("_")[-1])
    await state.update_data(rating_id=rating_id)
    rating = get_rating_by_id(rating_id)
    if isinstance(rating, Exception):
        await callback.message.edit_text(
            "Rating not found. Select options:", reply_markup=start_keyboard()
        )
        return

    await callback.message.edit_text(
        f"Rating '{rating.name}' loaded successfully!",
        reply_markup=rating_menu_keyboard(rating_id),
    )
    await state.set_state(RatingStates.rating_menu)


@dp.callback_query(F.data == "add_participant")
async def add_participant(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RatingStates.add_participant)
    await callback.message.edit_text(
        "Please enter the participant's name:",
        reply_markup=return_to_rating_menu_keyboard(),
    )


@dp.message(RatingStates.add_participant, F.text)
async def receive_participant_name(message: Message, state: FSMContext):
    data = await state.get_data()
    rating_id = data.get("rating_id")
    participant_name = message.text

    participant = create_rating_participant_by_name(rating_id, participant_name)
    if isinstance(participant, Exception):
        await message.answer(
            f"Participant '{participant_name}' already exists in the rating.",
            reply_markup=rating_menu_keyboard(rating_id),
        )
        return

    await message.answer(
        f"Participant '{participant_name}' added successfully!",
        reply_markup=rating_menu_keyboard(rating_id),
    )
    await state.set_state(RatingStates.rating_menu)


@dp.callback_query(F.data.startswith("show_participant_statistics_"))
async def show_participant_statistics(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    rating_id = data.get("rating_id")
    participant_id = int(callback.data.split("_")[-1])
    await state.update_data(participant_id=participant_id)
    stats = get_participant_statistics(participant_id)
    if isinstance(stats, Exception):
        await callback.message.edit_text(
            "Participant not found. Select options:",
            reply_markup=rating_menu_keyboard(rating_id),
        )
        return

    formatted_stats = f"""
Player: {stats.player.name}
Rating: {stats.rating_value}
Total games: {stats.played_games}
Total wins: {stats.wins}
Total losses: {stats.losses}
Win Rate: {stats.win_rate * 100:.2f}%
    """

    await callback.message.edit_text(
        formatted_stats,
        reply_markup=player_profile_keyboard(),
    )


@dp.callback_query(F.data == "delete_participant")
async def delete_participant(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    rating_id = data.get("rating_id")
    participant_id = data.get("participant_id")
    exc = delete_rating_participant(rating_id, participant_id)
    if isinstance(exc, Exception):
        await callback.message.edit_text(
            "Participant not found. Select options:",
            reply_markup=rating_menu_keyboard(rating_id),
        )
        return

    await callback.message.edit_text(
        "Participant deleted successfully. Select options:",
        reply_markup=rating_menu_keyboard(rating_id),
    )


@dp.callback_query(F.data == "add_game")
async def add_game(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    rating_id = data.get("rating_id")
    participants = get_rating_participants(rating_id)
    game_participant_selection = {participant.id: False for participant in participants}
    await state.update_data(game_participant_selection=game_participant_selection)

    if len(participants) < 2:
        await callback.message.edit_text(
            "Not enough participants to start a game.\nPlease add more participants.",
            reply_markup=rating_menu_keyboard(rating_id),
        )
        return
    await state.set_state(RatingStates.select_players)
    await callback.message.edit_text(
        "Select players for this game:",
        reply_markup=select_players_keyboard(game_participant_selection),
    )


@dp.callback_query(F.data.startswith("select_player_"))
async def select_player(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    game_participant_selection = data.get("game_participant_selection")
    player_id = int(callback.data.split("_")[-1])

    game_participant_selection[player_id] = not game_participant_selection[player_id]

    await state.update_data(game_participant_selection=game_participant_selection)
    await callback.message.edit_text(
        "Select players for this game:",
        reply_markup=select_players_keyboard(game_participant_selection),
    )


@dp.callback_query(F.data == "start_ranking")
async def start_ranking(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    game_participant_selection = data.get("game_participant_selection")
    selected = [
        player_id
        for player_id, selected in game_participant_selection.items()
        if selected
    ]

    if len(selected) < 2:
        await callback.message.edit_text(
            "Please select at least two players.",
            reply_markup=select_players_keyboard(game_participant_selection),
        )
        return
    participant_leaderboard = {player_id: None for player_id in selected}
    await state.update_data(participant_leaderboard=participant_leaderboard)
    await state.set_state(RatingStates.assign_ranks)
    await callback.message.edit_text(
        "Assign ranks to players:",
        reply_markup=assign_rank_keyboard(participant_leaderboard),
    )


@dp.callback_query(F.data.startswith("rank_"))
async def rank_game_participant(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    game_participant_id = int(callback.data.split("_")[-1])
    participant_leaderboard = data.get("participant_leaderboard")

    await callback.message.edit_text(
        "Assign rank to player:",
        reply_markup=rank_game_participant_keyboard(
            participant_leaderboard, game_participant_id
        ),
    )


@dp.callback_query(F.data.startswith("assign_rank_"))
async def assign_rank(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    game_participant_id = int(callback.data.split("_")[-2])
    rank = int(callback.data.split("_")[-1])
    participant_leaderboard = data.get("participant_leaderboard")
    participant_leaderboard[game_participant_id] = rank
    await state.update_data(participant_leaderboard=participant_leaderboard)
    await callback.message.edit_text(
        "Assign ranks to players:",
        reply_markup=assign_rank_keyboard(participant_leaderboard),
    )


@dp.callback_query(F.data == "finish_ranking")
async def finish_ranking(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    rating_id = data.get("rating_id")
    participant_leaderboard = data.get("participant_leaderboard")
    exc = create_game_with_rankings(participant_leaderboard, rating_id)
    if isinstance(exc, Exception):
        await callback.message.edit_text(
            "Failed to create game. Please try again.",
            reply_markup=rating_menu_keyboard(rating_id),
        )
        return

    await callback.message.edit_text(
        "Game created successfully!", reply_markup=rating_menu_keyboard(rating_id)
    )
    await state.set_state(RatingStates.rating_menu)


@dp.callback_query(F.data == "return_to_start")
async def return_to_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RatingStates.start)
    await callback.message.edit_text(
        "Welcome to the Bot! This bot allows you to create, manage, and play ratings. It has the following main functions:\n\n"
        "1. Create a new rating: This allows you to create a new rating system. You can give it a unique name and add participants to the rating.\n\n"
        "2. Load an existing rating: If you have created a rating before, you can load it and start managing it further.\n\n"
        "3. Play a game: If you have a rating with at least two participants, you can start a game to assign ranks to the participants.\n\n"
        "To get started, please choose an option below:",
        reply_markup=start_keyboard(),
    )


@dp.callback_query(F.data == "return_to_rating_menu")
async def return_to_rating_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    rating_id = data.get("rating_id")
    await state.set_state(RatingStates.start)
    await callback.message.edit_text(
        "Choose an option:", reply_markup=rating_menu_keyboard(rating_id)
    )


if __name__ == "__main__":
    init_db()
    dp.run_polling(bot, skip_updates=True)
