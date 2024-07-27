import os
import telebot
from telebot import types
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
tb = telebot.TeleBot(token=os.environ.get("BOT_TOKEN"))
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
response = types.Message # Create message object

if __name__ == "__main__":
    # Welcome message
    @tb.message_handler(commands=["start"])
    def send_welcome(response):
        tb.reply_to(response, "Hi there, I am Asian Fleming, your virtual physics assistant!")
        tb.send_message(response.chat.id, "How may I help?")

    # ChatGPT response
    @tb.message_handler()
    def openai(response):
        completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI assistant named Asian Fleming, created by Ariq Koh, skilled in explaining Physics concepts under the Singapore H2/H1 A Levels syllabus. Your replies should only be in text with no formatting. Your answers should be relevant to the latest syllabus."},
            {"role": "user", "content": response.text}
            ])
        tb.reply_to(response, completion.choices[0].message.content)

    tb.infinity_polling()