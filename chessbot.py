import logging
import pygame
import chess
import chess.svg
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from io import BytesIO
from inspect import getsourcefile
from os.path import abspath
from telegram.ext import Application, CommandHandler, Updater, MessageHandler, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Bot, InputFile
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

def get_path(path):
    return abspath(getsourcefile(lambda:0)).rstrip("chessbot.py")+path


def draw_board():
  pass

async def start(update, context):
    context.move_data = None
    await update.message.reply_text('Привет. Это телеграмм бот для игры в шамхматы. для большей информации - /help')


async def help(update, context):  # WIP
    await update.message.reply_text('WIP')


async def messageHandler(update, context):
    global board
    text = update.message.text
    await make_move(update, context, text)


async def start_match(update, context):
    await update.message.reply_text('Начинаю игру', reply_markup=markup1)
    await send_board(update, context)
    

async def from_uci(update, context, text):
    global board
    try:
        move = chess.Move.from_uci(text)
        if move in board.legal_moves:
            return move
        else:
            await update.message.reply_text("invalid move")
            return False
    except Exception as e:
        await update.message.reply_text("invalid move   " + str(e))
        return False


async def make_move(update, context, text):
    move = await from_uci(update, context, text)
    if move:
        board.push(move)
    await send_board(update, context)


async def send_board(update, context):
    global board

    svg_board = chess.svg.board(board=board)
    with open("svg_board.svg", "w") as f:
        f.write(svg_board)
    drawing = svg2rlg("svg_board.svg")
    renderPM.drawToFile(drawing, "png_board.png", fmt="PNG")

    await update.message.reply_photo("png_board.png")



def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("start_match", start_match))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messageHandler))

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
