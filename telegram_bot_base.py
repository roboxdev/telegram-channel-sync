import os
from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from queue import Queue
from typing import Optional

from telegram import Bot, Message, User, InlineKeyboardMarkup, Update
from telegram.ext import Dispatcher, CallbackContext, Updater

BOT_TOKEN = os.environ['BOT_TOKEN']
APP_TOKEN = os.environ.get('APP_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

LOG_CHAT_ID = int(os.environ['LOG_CHAT_ID'])


@dataclass
class TelegramBotBase:
    dispatcher: Dispatcher = None
    bot: Bot = None
    _log_series_enabled: bool = False
    _log_message: Optional[Message] = None

    def __post_init__(self):
        queue = Queue()
        self.dispatcher = self.dispatcher or Dispatcher(
            bot=Bot(token=BOT_TOKEN),
            update_queue=queue,
        )
        self.bot = self.dispatcher.bot
        self.dispatcher.add_error_handler(self.error_callback)
        self.set_handlers(self.dispatcher)

    @abstractmethod
    def set_handlers(self, dispatcher: Dispatcher):
        pass

    @staticmethod
    def get_user_info(user: User):
        user_info = f'<b><a href="tg://user?id={user.id}">{user.full_name}</a></b> ' \
                    f'<i>(id <a href="https://t.me/@id{user.id}">{user.id}</a>)</i>'
        if username := user.username:
            user_info += f' @{username}'
        return user_info

    def log(
            self,
            message: str,
            user: User = None,
            silent: bool = True,
            reply_markup: InlineKeyboardMarkup = None,
    ):
        text = message
        if user:
            text += f'\n\nby {self.get_user_info(user)}'

        message_params = dict(
            chat_id=LOG_CHAT_ID,
            parse_mode='HTML',
            reply_markup=reply_markup,
        )
        if self._log_series_enabled and (log_message := self._log_message):
            self._log_message = self.bot.edit_message_text(
                **message_params,
                text=f'{log_message.text}\n{text}',
                message_id=log_message.message_id,
            )
        else:
            self._log_message = self.bot.send_message(
                **message_params,
                text=text,
                disable_notification=silent,
            )

    @contextmanager
    def logging_series(self):
        self._log_series_enabled = True
        self._log_message = None
        yield self.log
        self._log_message = None
        self._log_series_enabled = False

    def error(self, *args, **kwargs):
        self.log(*args, **kwargs, silent=False)

    def error_callback(self, update: object, context: CallbackContext):
        error = context.error
        message = f'⚠️ {error}'
        self.error(message=message)
        raise error

    @staticmethod
    def set_webhook():
        updater = Updater(token=BOT_TOKEN)
        updater.bot.set_webhook(WEBHOOK_URL)

    @classmethod
    def start_polling(cls):
        updater = Updater(token=BOT_TOKEN)
        telegram_bot = cls(dispatcher=updater.dispatcher)
        updater.bot.delete_webhook()
        updater.start_polling()

    @classmethod
    def process_webhook_request(cls, data):
        telegram_bot = cls()
        update = Update.de_json(data, telegram_bot.bot)
        telegram_bot.dispatcher.process_update(update)
        return 'ok'

    @classmethod
    def process_request(cls, data):
        # TODO
        return 'OK'

    @classmethod
    def process_gcf_call(cls, request):
        data = request.args if request.method == 'GET' else request.get_json(
            force=True
        )
        if 'update_id' in data:
            return cls.process_webhook_request(data)
        if (token := data.get('token', '')) and (token == APP_TOKEN):
            return cls.process_request(data)
        else:
            return 'Forbidden'
