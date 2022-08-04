import json
import os
import logging
import re
from dataclasses import dataclass

from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    User,
)
from telegram.ext import (
    Dispatcher,
    Filters,
    MessageHandler,
    CallbackContext,
    CallbackQueryHandler,
)
from telegram.update import Update

from telegram_bot_base import TelegramBotBase
from post_parser import PostParser, PostData
from gitlab_post import GitlabPost

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

CHANNEL_ID = int(os.environ['CHANNEL_ID'])


@dataclass
class TelegramBot(TelegramBotBase):
    def set_handlers(self, dispatcher: Dispatcher):
        message_filters = Filters.chat(
            chat_id=CHANNEL_ID) & ~Filters.status_update & ~Filters.forwarded
        message_handler = MessageHandler(
            filters=message_filters,
            callback=self.chat_message_handler,
        )
        dispatcher.add_handler(message_handler)

        channel_post_command_query_callback = CallbackQueryHandler(
            callback=self.channel_post_command_callback_query,
        )
        dispatcher.add_handler(channel_post_command_query_callback)

    @staticmethod
    def get_delete_attempt_button(post_id: int):
        return InlineKeyboardButton(
            text='🗑 Удалить',
            callback_data=json.dumps({
                'command': 'attempt_to_delete',
                'post_id': post_id,
            }),
        )

    def create_post(self, post_id: int, post_data: PostData):
        GitlabPost(post_id=post_id).create_or_update(
            post_data=post_data,
            is_update=False,
        )
        self.log(
            message=f'🆕 #{post_id} <a href="{post_data["link"]}">'
                    f'{post_data["title"]}'
                    f'</a>',
            reply_markup=InlineKeyboardMarkup([[
                self.get_delete_attempt_button(post_id=post_id)
            ]]),
        )

    def update_post(self, post_id: int, post_data: PostData):
        GitlabPost(post_id=post_id).create_or_update(
            post_data=post_data,
            is_update=True,
        )
        self.log(
            message=f'🔃 #{post_id} <a href="{post_data["link"]}">'
                    f'{post_data["title"]}'
                    f'</a>',
        )

    def delete_post(self, post_id: int, user: User = None):
        GitlabPost(post_id=post_id).delete()
        self.bot.delete_message(
            chat_id=CHANNEL_ID,
            message_id=post_id,
        )
        self.error(
            message=f'🗑 #{post_id}',
            user=user,
        )

    def chat_message_handler(self, update: Update, context: CallbackContext):
        message = update.effective_message
        post_id = message.message_id
        parser = PostParser(message)
        if fallback_title := parser.fallback_title:
            self.error(f'Set proper title!\n\n'
                       f'Fallback title set:\n'
                       f'{fallback_title}')

        if is_update := bool(update.edited_channel_post):
            self.update_post(post_id=post_id, post_data=parser.post_data)
        else:
            self.create_post(post_id=post_id, post_data=parser.post_data)

    def channel_post_command_callback_query(self, update, context):
        data = json.loads(update.callback_query.data)
        command = data.get('command')

        if command == 'attempt_to_delete':
            update.callback_query.answer('Confirmation required')

            delete_button = InlineKeyboardButton(
                text='🗑 Удалить',
                callback_data=json.dumps({
                    'command': 'delete',
                    'post_id': data['post_id'],
                }),
            )
            cancel_button = InlineKeyboardButton(
                text='❌ Отмена',
                callback_data=json.dumps({
                    'command': 'cancel_delete',
                    'post_id': data['post_id'],
                }),
            )
            update.callback_query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup([[
                    delete_button,
                    cancel_button,
                ]])
            )

        if command == 'delete':
            update.callback_query.answer('Deleting...')
            user = update.effective_user
            self.delete_post(post_id=data['post_id'], user=user)
            update.callback_query.edit_message_reply_markup()
            update.callback_query.answer('Deleted')

        if command == 'cancel_delete':
            update.callback_query.answer('Deletion cancelled')
            update.callback_query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup([[
                    self.get_delete_attempt_button(post_id=data['post_id']),
                ]])
            )


if __name__ == '__main__':
    TelegramBot.start_polling()
