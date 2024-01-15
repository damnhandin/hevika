from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.models.postgresql import Database


class ChannelInteractions:
    @classmethod
    async def add_bank_to_channel(cls, bot: Bot, bank_id, db: Database, channel_id, bot_tag):
        bank = await db.select_bank_by_id(bank_id)
        preview_text = f"{bank['bank_name']}!\n" \
                       f"{bank['bank_description']}"
        photo_id = bank["bank_photo"]
        bank_url = bank["bank_url"]
        open_in_bot_url = f"https://t.me/{bot_tag}?start=0t{bank['bank_id']}"
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти на страницу банка",
                                  url=bank_url)],
            [InlineKeyboardButton(text="Подробнее в боте",
                                  url=open_in_bot_url)]
        ])
        post_id = await bot.send_photo(chat_id=channel_id,
                                       caption=preview_text,
                                       photo=photo_id,
                                       reply_markup=reply_markup)
        await db.add_post_to_bd(bank_id, channel_id, post_id)