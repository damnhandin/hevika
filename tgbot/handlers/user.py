from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.config import Config
from tgbot.misc.misc_commands import format_channel_link
from tgbot.models.postgresql import Database


async def user_start(message: Message, db: Database, config: Config):
    user = await db.select_user_tg_id(telegram_id=message.from_user.id)
    tg_user = message.from_user
    if not user:
        await db.add_user(username=tg_user.username,
                          first_name=tg_user.first_name,
                          last_name=tg_user.last_name,
                          full_name=tg_user.full_name,
                          telegram_id=tg_user.id)
    link = await format_channel_link(config.tg_bot.channel_tag)
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Показать все бесплатные банки",
                              url=link)]
    ])
    await message.answer(f"Приветствую тебя, {tg_user.full_name}! 👋\n"
                         f"Я помогу тебе найти беспроцентные займы в пару кликов! 😉"
                         f"Для взаимодействия используй кнопки снизу 👇", reply_markup=reply_markup)


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
