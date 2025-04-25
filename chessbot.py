import logging
import pygame
import chess
import chess.svg
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from io import BytesIO
from inspect import getsourcefile
from os.path import abspath
from telegram.ext import (
    Application,
    CommandHandler,
    Updater, 
    MessageHandler, 
    filters, 
    ContextTypes,
    CallbackQueryHandler)
from telegram import (ReplyKeyboardMarkup, 
                      ReplyKeyboardRemove, 
                      KeyboardButton, 
                      Bot, 
                      InputFile, 
                      InlineKeyboardButton,
                      InlineKeyboardMarkup)
from random import randint
from config import BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

bot = Bot(BOT_TOKEN)

chess_piece_sets = [
    "alpha",
    "anarcandy",
    "caliente",
    "california",
    "cardinal",
    "cburnett",
    "celtic",
    "chess7",
    "chessnut",
    "companion",
    "cooke",
    "disguised",
    "dubrovny",
    "fantasy",
    "firi",
    "fresca",
    "gioco",
    "governor",
    "horsey",
    "icpieces",
    "kiwen-suwi",
    "kosal",
    "leipzig",
    "letter",
    "maestro",
    "merida",
    "monarchy",
    "mono",
    "mpchess",
    "pirouetti",
    "pixel",
    "reillycraig",
    "rhosgfx",
    "riohacha",
    "shapes",
    "spatial",
    "staunty",
    "tatiana",
    "xkcd"
]

layout1 = [["move"]]
markup1 = ReplyKeyboardMarkup(layout1, one_time_keyboard=False)

games = {}
"""
games = {
chat_id: {"board": chess.Board(), "players": (user1_id, user2_id or None)}
}
"""

def get_path(path):
    return abspath(getsourcefile(lambda:0)).rstrip("chessbot.py")+path


async def start(update, context):
    context.move_data = None
    await update.message.reply_text('Привет. Это телеграмм бот для игры в шамхматы. для большей информации - /help')


async def help(update, context):  # WIP
    await update.message.reply_text('WIP')

"""async def from_uci(update, context, text):
    global board
    try:
        move = chess.Move.from_uci(update, context, text)
        if move in board.legal_moves:
            return move
        else:
            await update.message.reply_text("invalid move")
            return False
    except Exception as e:
        await update.message.reply_text("invalid move   " + str(e))
        return False"""

async def do_move(update, context, text):
    try:
        chat = update.effective_chat
        board = games[chat.id]["board"]
        move = board.parse_uci(text.lower())
        board.push(move)
        await send_board(update, context)
    except Exception as e:
        await update.message.reply_text("Invalid move!" + str(e))

async def message_handler(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.message.text

    if chat.id not in games:
        await update.message.reply_text("Начните игру с помощью /start_game")
        return
    
    game = games[chat.id]
    board = game["board"]

    if board.is_game_over():
        await update.message.reply_text("Игра закончилась! Начните новую с помощью /start_game")
        return
    
    if chat.type == "private":
        await do_move(update, context, message)
    else:
        white, black = game["players"]
        current_color, current_player = ("белых", white) if board.turn == chess.WHITE else ("чёрных", black)
        cur_user_name = await (context.bot.get_chat_member(chat.id, game['players'][0]) if current_color == "белых" 
                               else context.bot.get_chat_member(chat.id, game['players'][0]))
        
        cur_user_name = cur_user_name.user.username or cur_user_name.user.name
        if user.id != current_player:
            await update.message.reply_text(f"Сейчас не ваш ход! Сейчас ходит @{cur_user_name}, играющий за {current_color}")
            return
        
        await do_move(update, context, message)

async def start_game(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        games[chat.id] = {
            "board": chess.Board(),
            "players": (user.id, None),
        }
        await send_board(update, context, "Начинаю игру, 2 игрока на одном устройстве.")
    else: # chat.type = "group"
        inline_keyboard = [[InlineKeyboardButton("Присоединиться за белых", callback_data="join_white")],
                           [InlineKeyboardButton("Присоединиться за чёрных", callback_data="join_black")]]
        await update.message.reply_text("Начинаю игру, ожидаю 2 игрков.",
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard))
        games[chat.id] = {
            "board": chess.Board(),
            "players": (None, None),
            "message_id": update.message.message_id
        }

async def handle_join(update, context):
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user = query.from_user
    user_name = user.username

    if chat_id not in games:
        await query.answer("Игра не найдена.")
        return
    
    game = games[chat_id]

    white, black = game["players"]

    if "join_white" in query.data and white is None:
        game["players"] = (user_id, black)
        user = await context.bot.get_chat_member(chat_id, game['players'][0])
        user_name = user.user.username or user.user.name
        await context.bot.send_message(chat_id, f"{user_name} присоединился за белых.")
    elif "join_black" in query.data and black is None:
        game["players"] = (white, user_id)
        user = await context.bot.get_chat_member(chat_id, game['players'][1])
        user_name = user.user.username or user.user.name
        await context.bot.send_message(chat_id, f"{user_name} присоединился за чёрных.")
    else:
        await query.answer("сторона занята.")
        return
    
    if None not in game["players"]:
        white = await context.bot.get_chat_member(chat_id, game['players'][0])
        black = await context.bot.get_chat_member(chat_id, game['players'][1])
        
        white_name = white.user.username or white.user.name
        black_name = black.user.username or black.user.name
        try:
            await query.message.delete()
        except:
            pass
        response = f"Игра началась!\n {white_name} играет за белых\n {black_name} играет за чёрных"
        await send_board(update, context)

    try:
        await query.edit_message_text(response, 
                                      chat_id=chat_id,
                                      message_id=game["message_id"])
    except Exception as e:
        # Fallback if message can't be edited
        await context.bot.send_message(chat_id, response)

async def send_board(update, context, capt=None):
    chat = update.effective_chat

    if chat.id not in games:
        await update.message.reply_text("Игра не найдена.")
        return

    board = games[chat.id]["board"]

    svg_board = chess.svg.board(board=board)
    with open("svg_board.svg", "w") as f:
        f.write(svg_board)
    drawing = svg2rlg("svg_board.svg")
    png_bytes = BytesIO()
    renderPM.drawToFile(drawing, png_bytes, fmt="PNG")
    png_bytes.seek(0)

    if update.message:
        await update.message.reply_photo(photo=png_bytes, caption=capt)
    else:
        await context.bot.send_photo(photo=png_bytes, chat_id=chat.id, caption=capt)


async def check_game_status(update, context):
    global board
    caption = None
    if board.is_check():
        caption = "Шах!"
    if board.is_game_over():
        if board.is_checkmate():
            winner = "Чёрные" if chess.Outcome.result == "1-0" else "Белые"
            caption = f"Победили {winner}"
        elif board.is_stalemate():
            caption = "Пат! Ничья!"
        elif board.is_insufficient_material():
            caption = "Недостаточно материала! Ничья!"
        elif board.is_seventyfive_moves():
            caption = "Ничья по правилу 75-ходов!"
        elif board.is_fivefold_repetition():
            caption = "Ничья по троекратному повторению позиции!"
    return caption


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("start_game", start_game))
    application.add_handler(CommandHandler("create_game", start_game))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(CallbackQueryHandler(handle_join))

    application.run_polling()


if __name__ == '__main__':
    board = chess.Board()
    
    pygame.init()
    size = (256, 256)
    surface = pygame.Surface(size)
    surface.fill((255, 255, 255))
    pygame.image.save(surface, get_path("data/test.png"))
    piece_id = [["wB", "wK", "wN", "wP", "wQ", "wR"],     # piece_id[0][...] -> white piece
                ["bB", "bK", "bN", "bP", "bQ", "bR"]]    # piece_id[1][...] -> black piece
                                                        # ORDER -  Bishop, King, Knight, Pawn, Queen, Rook
    piece_png = [list(map(lambda x: x + ".png", piece_id[0])), list(map(lambda x: x + ".png", piece_id[1]))]
    piece_set = "merida" # piece picture set
    piece_path = [list(map(lambda x: get_path(f"data/pieces/{piece_set}/{x}"), piece_png[0])), list(map(lambda x: get_path(f"data/pieces/{piece_set}/{x}"), piece_png[1]))]
    main()
