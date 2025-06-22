import sys
import os
import traceback
from dotenv import load_dotenv
from flask import Flask, request
import telebot
from openai import OpenAI
import base64
import requests


# Load environment variables
load_dotenv()
TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Heroku app URL with the path to the webhook
CHAT_CONFIG = os.environ.get("CHAT_CONFIG")

# Initialize Telegram bot and OpenAI
tb = telebot.TeleBot(token=TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)
temp_history = {}

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
        username = message.from_user.username
        if username not in temp_history:
            temp_history[username] = "Chat history:\n"
        client_input = temp_history[username] + "\ncurrent message: " + message.text
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": CHAT_CONFIG},
                {"role": "user", "content": client_input}
            ]
        )
        reply_text = response.choices[0].message.content
        temp_history[username] += f"Message: {message.text}, Response: {reply_text}\n"
        tb.reply_to(message, reply_text)
        sys.stdout.write(f"\nuser: {message.from_user.username}\nMessage: {message.text}\nResponse: {reply_text} ")
        sys.stdout.write(f"\nHistory: {temp_history[username]}\n")

    except Exception as e:
        tb.reply_to(message, "Sorry, the server is currently offline. Please try again later.")
        sys.stdout.write(f"Error occurred: {e}")
        sys.stdout.write(traceback.format_exc())


@tb.message_handler(content_types=["photo"])
def handle_photo(message):
    try:
        username = message.from_user.username or str(message.from_user.id)
        file_info = tb.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"

        # Download the image
        response = requests.get(file_url)
        image_bytes = response.content

        # Convert to base64 for OpenAI if needed
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Prompt to ask with the image
        prompt = "Explain this image to a student."

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": CHAT_CONFIG},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ]
        )

        reply_text = response.choices[0].message.content
        tb.reply_to(message, reply_text)
        sys.stdout.write(f"\nUser: {username}\nPhoto analyzed. Response: {reply_text}\n")

    except Exception as e:
        tb.reply_to(message, "Sorry, I couldn't process the image.")
        sys.stdout.write(f"Error handling photo: {e}\n")
        sys.stdout.write(traceback.format_exc())


if __name__ == "__main__":
    tb.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    from waitress import serve
    serve(app, host='0.0.0.0', port=port)