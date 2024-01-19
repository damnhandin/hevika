import logging
from typing import Union

from aiogram import types
from aiogram.types import InputMedia, ContentType
from aiogram.utils.exceptions import MessageNotModified
import aiogram.utils.markdown as fmt


async def format_channel_link(channel_tag):
    return f"t.me/{channel_tag}"


async def format_bank_text(bank, bank_rating, is_notification=False):
    if is_notification is True:
        bank_text = fmt.hbold("Появились новые возможности! 🎉\n\n")
    else:
        bank_text = ""

    if not bank:
        return "Для взаимодействия используйте кнопки снизу 👇"
    bank_name = bank["bank_name"]
    bank_desc = bank["bank_description"]
    if bank_rating == 0:
        rating_text = "Без рейтинга ⭐️"
    else:
        rating_text = f"Рейтинг: {bank_rating:0.1f} / 5.0 ⭐️"

    bank_text += f"{bank_name}\n\n" \
                 f"{bank_desc}\n\n" \
                 f"{rating_text}"

    return bank_text


async def smart_message_interaction_photo(target: Union[types.Message, types.CallbackQuery], reply_markup,
                                          msg_text: str = None,
                                          media_file_id: str = None):
    if media_file_id:
        media_file = InputMedia(media=media_file_id, caption=msg_text)
    else:
        media_file = None
    if isinstance(target, types.CallbackQuery):
        target: types.CallbackQuery
        if target.message.content_type == ContentType.TEXT:
            if media_file:
                try:
                    await target.message.answer_photo(photo=media_file.media,
                                                      caption=media_file.caption,
                                                      reply_markup=reply_markup)
                except:
                    try:
                        await target.message.edit_text(text=msg_text,
                                                       reply_markup=reply_markup)
                    except MessageNotModified:
                        pass
                    except Exception as exc:
                        logging.info(f"{exc}", exc_info=True)

                        await target.message.answer(text=msg_text,
                                                    reply_markup=reply_markup)
            else:
                try:
                    await target.message.edit_text(text=msg_text,
                                                   reply_markup=reply_markup)
                except MessageNotModified:
                    pass
                except Exception as exc:
                    logging.info(f"{exc}", exc_info=True)
                    try:
                        await target.message.answer_photo(photo=media_file.media,
                                                          caption=media_file.caption,
                                                          reply_markup=reply_markup)
                    except:
                        await target.message.answer(text=msg_text,
                                                    reply_markup=reply_markup)
        else:
            if media_file:
                try:
                    await target.message.edit_media(media=media_file,
                                                    reply_markup=reply_markup)
                except MessageNotModified:
                    pass
                except Exception as exc:
                    logging.info(f"{exc}", exc_info=True)
                    await target.message.answer_photo(photo=media_file.media,
                                                      caption=media_file.caption,
                                                      reply_markup=reply_markup)
            else:
                await target.message.answer(text=msg_text,
                                            reply_markup=reply_markup)
    else:
        if media_file:
            await target.answer_photo(photo=media_file.media, caption=media_file.caption,
                                      reply_markup=reply_markup)
        else:
            await target.answer(text=msg_text,
                                reply_markup=reply_markup)

    return


async def select_func_and_count_banks(menu, db, user_tg_id):
    if menu == "bank_preview":
        bank_func = db.select_bank_offset
        amount_of_pages = await db.count_amount_of_bank_pages(user_tg_id)
    elif menu == "tagged":
        bank_func = db.select_user_tag_bank
        amount_of_pages = await db.count_amount_of_user_banks_tag(user_tg_id)
    else:
        # menu == "favorties"
        bank_func = db.select_user_fav_bank
        amount_of_pages = await db.count_amount_of_user_banks_fav(user_tg_id)

    return bank_func, amount_of_pages
