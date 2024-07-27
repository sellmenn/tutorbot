import os
from flask import Flask, request
import telebot
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize bot and OpenAI client
TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Your Heroku app URL with the path to the webhook

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
    tb.send_message(message.chat.id, "How may I help?")

@tb.message_handler()
def handle_message(message):
    try:
        response = client.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI assistant named Asian Fleming, created by Ariq Koh, skilled in explaining Physics concepts under the Singapore H2/H1 A Levels syllabus. Your replies should only be in text with no formatting. Your answers should be relevant to the latest syllabus."},
                {"role": "user", "content": message.text}
            ]
        )
        reply_text = response.choices[0].message['content']
        tb.reply_to(message, reply_text)
    except Exception as e:
        tb.reply_to(message, "Sorry, something went wrong. Please try again later.")

if __name__ == "__main__":
    # Set up webhook
    tb.set_webhook(url=WEBHOOK_URL)
    # Run Flask application
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))