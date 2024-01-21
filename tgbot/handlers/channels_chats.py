from aiogram import Dispatcher, types
from aiogram.types import ContentType
from tgbot.filters.group_filter import GroupFilter


async def bot_in_chat_handler(message: types.Message):
    return


async def bot_in_channel_handler(*args, **kwargs):
    return


def register_channel_and_chats(dp: Dispatcher):
    dp.register_channel_post_handler(bot_in_channel_handler, content_types=ContentType.ANY,
                                     state="*")
    dp.register_message_handler(bot_in_chat_handler, GroupFilter(is_group=True),
                                content_types=ContentType.ANY, state="*")

