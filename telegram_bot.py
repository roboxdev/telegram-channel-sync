import os
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
from post import Post
from gitlab_post import GitlabPost

CHANNEL_ID = int(os.environ['CHANNEL_ID'])


@dataclass
class TelegramBot(TelegramBotBase):
    def set_handlers(self, dispatcher: Dispatcher):
        channel_post_message_filter = (
            Filters.chat(chat_id=CHANNEL_ID) &
            ~Filters.status_update &
            ~Filters.forwarded
        )
        channel_post_message_handler = MessageHandler(
            filters=channel_post_message_filter,
            callback=self.channel_post_message_handler,
        )
        dispatcher.add_handler(channel_post_message_handler)

        channel_post_forward_message_filter = (
            Filters.chat_type.private &
            # Filters.user(user_id=OWNER_ID) &
            Filters.forwarded &
            Filters.forwarded_from(chat_id=CHANNEL_ID)
        )
        channel_post_forward_message_handler = MessageHandler(
            filters=channel_post_forward_message_filter,
            callback=self.forward_message_handler,
        )
        dispatcher.add_handler(channel_post_forward_message_handler)

        channel_post_command_query_callback = CallbackQueryHandler(
            callback=self.channel_post_command_callback_query,
        )
        dispatcher.add_handler(channel_post_command_query_callback)

    @staticmethod
    def get_delete_attempt_button(post_id: int):
        return InlineKeyboardButton(
            text='🗑',
            callback_data=f'del_attempt|{post_id}',
        )

    def create_or_update_post(self, post: Post, is_update: bool = False):
        GitlabPost.from_post(post).create_or_update(
            is_update=is_update,
        )
        icon = '🔃' if is_update else '🆕'
        self.log(
            message=f'{icon} #{post.post_id} <a href="{post.message_link}">'
                    f'{post.title}'
                    f'</a>',
            reply_markup=InlineKeyboardMarkup([[
                self.get_delete_attempt_button(post_id=post.post_id)
            ]]),
        )

    def delete_post(self, post_id: int, user: User = None):
        GitlabPost.from_id(post_id=post_id).delete()
        self.bot.delete_message(
            chat_id=CHANNEL_ID,
            message_id=post_id,
        )
        self.error(
            message=f'🗑 #{post_id}',
            user=user,
        )

    def channel_post_message_handler(self, update: Update, context: CallbackContext):
        message = update.effective_message
        post = Post.from_message(message)
        is_update = bool(update.edited_channel_post or post.is_forward)
        self.create_or_update_post(post=post, is_update=is_update)

        if fallback_title := post.fallback_title:
            self.error(f'Set proper title!\n\n'
                       f'Fallback title set:\n'
                       f'{fallback_title}')

    def forward_message_handler(self, update: Update, context: CallbackContext):
        self.channel_post_message_handler(update=update, context=context)

    def command_del_attempt(
        self,
        *args,
        update: Update,
        context: CallbackContext,
    ):
        post_id, *_ = args
        update.callback_query.answer('Confirmation required')

        delete_button = InlineKeyboardButton(
            text='🗑',
            callback_data=f'del|{post_id}',
        )
        cancel_button = InlineKeyboardButton(
            text='❌',
            callback_data=f'del_cancel|{post_id}',
        )
        update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([[
                delete_button,
                cancel_button,
            ]])
        )

    def command_del(
        self,
        *args,
        update: Update,
        context: CallbackContext,
    ):
        post_id, *_ = args
        update.callback_query.answer('Deleting...')
        user = update.effective_user
        self.delete_post(post_id=post_id, user=user)
        update.callback_query.edit_message_reply_markup()
        update.callback_query.answer('Deleted')

    def command_del_cancel(
        self,
        *args,
        update: Update,
        context: CallbackContext,
    ):
        post_id, *_ = args
        update.callback_query.answer('Deletion cancelled')
        update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([[
                self.get_delete_attempt_button(post_id=post_id),
            ]])
        )

    def channel_post_command_callback_query(
        self,
        update: Update,
        context: CallbackContext,
    ):
        command_name, *command_args = update.callback_query.data.split('|')
        command = getattr(self, f'command_{command_name}')
        command(
            *command_args,
            update=update,
            context=context,
        )


if __name__ == '__main__':
    TelegramBot.start_polling()
