import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMedia
import aiogram.utils.markdown as fmt

from tgbot.models.postgresql import Database


class ChannelInteractions:
    @staticmethod
    async def format_preview_text(bank, bot_url):
        preview_text = f"{bank['bank_name']}!\n" \
                       f"{bank['bank_description']}\n\n" \
                       f"{fmt.hlink(title='Ссылка на бота для IPhone', url=bot_url)}"
        return preview_text

    @classmethod
    async def add_bank_to_channel(cls, bot: Bot, bank_id, db: Database, channel_id, bot_tag):
        bank = await db.select_bank_by_id(bank_id)
        open_in_bot_url = f"telegram.me/{bot_tag}?start=0t{bank['bank_id']}"
        preview_text = await cls.format_preview_text(bank, open_in_bot_url)
        photo_id = bank["bank_photo"]
        bank_url = bank["bank_url"]
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

    @classmethod
    async def update_bank_info(cls, bot: Bot, banks, bot_tag):
        for bank in banks:
            open_in_bot_url = f"telegram.me/{bot_tag}?start=0t{bank['bank_id']}"
            preview_text = await cls.format_preview_text(bank, open_in_bot_url)
            photo_id = bank["bank_photo"]
            bank_url = bank["bank_url"]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Перейти на страницу банка",
                                      url=bank_url)],
                [InlineKeyboardButton(text="Подробнее в боте",
                                      url=open_in_bot_url)]
            ])
            if photo_id:
                media_file = InputMedia(media=photo_id, caption=preview_text)
                try:
                    await bot.edit_message_media(chat_id=bank["channel_id"],
                                                 message_id=bank["post_id"],
                                                 media=media_file,
                                                 reply_markup=reply_markup)
                except Exception as exc:
                    logging.debug(f"{exc}", exc_info=True)
            else:
                try:
                    await bot.edit_message_text(chat_id=bank["channel_id"],
                                                message_id=bank["post_id"],
                                                text=preview_text,
                                                reply_markup=reply_markup)
                except Exception as exc:
                    logging.debug(f"{exc}", exc_info=True)