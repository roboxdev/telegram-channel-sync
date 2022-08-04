from telegram_bot import TelegramBot


def main(request):
    return TelegramBot.process_gcf_call(request)
