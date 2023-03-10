from django.shortcuts import render
from threading import Thread
from . import telegram_bot

def handle_telegram_bot(request):
    bot_thread = Thread(target=telegram_bot.run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    return render(request, 'lynx/index.html')
