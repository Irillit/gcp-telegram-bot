import os
import string
import random
import logging

from PIL import Image, ImageDraw, ImageFont
from google.cloud import vision
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


IMAGE_LIB = 'images'


class CatDetector:
    LABELS = ["Cat", "Dog", "Animal"]
    COLOURS = ["Cat"]

    def detect(self, filename) -> list:
        with open(filename, 'rb') as user_image:
            content = user_image.read()
        image = vision.Image(content=content)
        client = vision.ImageAnnotatorClient()
        objects = client.object_localization(image=image).localized_object_annotations
        result = []
        if len(objects) > 0:
            with Image.open(filename) as im:
                size = im.size
                draw = ImageDraw.Draw(im)
                font = ImageFont.truetype("open_sans.ttf", 18)
                for object_ in objects:
                    if object_.name in self.LABELS:
                        vertexes = []
                        result.append((object_.name, object_.score))
                        for vertex in object_.bounding_poly.normalized_vertices:
                            vertexes.append((size[0] * vertex.x, size[1] * vertex.y))
                        draw.rectangle((vertexes[0], vertexes[2]), outline=128)
                        draw.text(vertexes[0], f"{object_.name} {round(object_.score, 3)}", (252, 3, 78), font=font)
                im.save(filename)
        return result


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def photo(update: Update, context: CallbackContext) -> None:
    """Stores the photo and asks for a location."""
    user = update.message.from_user
    letters = string.ascii_lowercase
    LEN = 10
    filename = ''.join(random.choice(letters) for _ in range(LEN))
    filename = f"{IMAGE_LIB}/{filename}.jpg"
    photo_file = update.message.photo[-1].get_file()
    photo_file.download(filename)
    logger.info("Photo of %s: %s", user.first_name, filename)
    update.message.reply_text('Got image')

    detector = CatDetector()
    objects = detector.detect(filename)

    update.message.reply_photo(photo=open(filename, 'rb'))
    for object, score in objects:
        update.message.reply_text("{} confidence: {}".format(object, score))
    os.remove(filename)


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text("Uploading image")


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

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    dispatcher.add_handler(MessageHandler(Filters.photo, photo))

    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
