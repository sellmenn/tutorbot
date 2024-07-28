import sys
import os
import logging
from dotenv import load_dotenv
from flask import Flask, request
import telebot
from openai import OpenAI

# Load environment variables
load_dotenv()
TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Heroku app URL with the path to the webhook
CHAT_CONFIG = os.environ.get("CHAT_CONFIG")

# Initialize Telegram bot and OpenAI
tb = telebot.TeleBot(token=TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_str)
    tb.process_new_updates([update])
    return "OK", 200

@tb.message_handler(commands=["start"])
def send_welcome(message):
    tb.reply_to(message, "Hi there, I am Asian Fleming, your virtual physics assistant!")

@tb.message_handler(content_types=["text"])
def handle_message(message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": CHAT_CONFIG},
                {"role": "user", "content": message.text}
            ]
        )
        reply_text = response.choices[0].message.content
        tb.reply_to(message, reply_text)
        sys.stdout.write(f"user: {message.from_user.username}, Message: {message.text}, Response: {reply_text} ")

    except Exception as e:
        tb.reply_to(message, "Sorry, the server is currently offline. Please try again later.")
        sys.stdout.write(f"Error occurred: {e}")

@tb.message_handler(content_types=["photo"])
def handle_photo(message):
    tb.reply_to(message, "Sorry, I am currently unable to process photos.")

if __name__ == "__main__":
    tb.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    from waitress import serve
    serve(app, host='0.0.0.0', port=port)