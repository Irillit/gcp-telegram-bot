import os
import string
import random
import logging

from cat_dog_detector import CatDogDetector
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


IMAGE_DIR = 'images'
LENGTH = 10


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\! Load your image and I\'ll check cats on it',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Load your image and I\'ll check cats on it!')


def generate_filename():
    """generates random filename for one session use"""
    letters = string.ascii_lowercase
    filename = ''.join(random.choice(letters) for _ in range(LENGTH))
    filename = f"{IMAGE_DIR}/{filename}.jpg"
    return filename


def image(update: Update, context: CallbackContext) -> None:
    """Stores the image and asks for a location."""
    user = update.message.from_user
    filename = generate_filename()
    photo_file = update.message.photo[-1].get_file()
    photo_file.download(filename)
    logger.info("Photo of %s: %s", user.first_name, filename)
    update.message.reply_text('Got image')

    detector = CatDogDetector()
    objects = detector.detect(filename)

    update.message.reply_photo(photo=open(filename, 'rb'))
    for object, score in objects:
        update.message.reply_text("{} confidence: {}".format(object, score))
    os.remove(filename)


def main() -> None:
    with open('credentials.txt', 'r') as creds:
        token = creds.readline()
    if not token:
        logger.error("Token in credentials.txt is invalid!")
        quit(13)
    updater = Updater(token)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(Filters.photo, image))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
