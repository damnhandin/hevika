import logging
from typing import Union

from aiogram import Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMedia

from tgbot.config import Config
from tgbot.handlers.admin import format_bank_text
from tgbot.keyboards.callback_datas import bank_navg, bank_inter, act_callback
from tgbot.misc.misc_commands import format_channel_link
from tgbot.models.image_paginator import ImagePaginator
from tgbot.models.postgresql import Database


async def open_user_main_menu(target: Union[types.CallbackQuery, types.Message], config: Config):
    link = await format_channel_link(config.tg_bot.channel_tag)
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Карусель займов",
                              callback_data=bank_navg.new(
                                  act="user_bank_carousel",
                                  menu="bank_preview",
                                  c_p="1"))],
        [InlineKeyboardButton(text="Показать все бесплатные займы",
                              url=link)]
    ])
    if isinstance(target, types.CallbackQuery):
        await target.message.edit_text(
            f"Приветствую тебя, {target.from_user.full_name}! 👋\n"
            f"Я помогу тебе найти беспроцентные займы в пару кликов! 😉"
            f"Для взаимодействия используй кнопки снизу 👇", reply_markup=reply_markup)

    elif isinstance(target, types.Message):
        await target.answer(f"Приветствую тебя, {target.from_user.full_name}! 👋\n"
                            f"Я помогу тебе найти беспроцентные займы в пару кликов! 😉"
                            f"Для взаимодействия используй кнопки снизу 👇", reply_markup=reply_markup)
    else:
        print(f"Новый type попал в объект main menu target = {target}")


async def user_main_menu(cq, config, db):
    user = await db.select_user_tg_id(telegram_id=cq.from_user.id)
    tg_user = cq.from_user
    if not user:
        await db.add_user(username=tg_user.username,
                          first_name=tg_user.first_name,
                          last_name=tg_user.last_name,
                          full_name=tg_user.full_name,
                          telegram_id=tg_user.id)
    await open_user_main_menu(cq, config)


async def user_start(message: Message, db: Database, config: Config):
    user = await db.select_user_tg_id(telegram_id=message.from_user.id)
    tg_user = message.from_user
    if not user:
        await db.add_user(username=tg_user.username,
                          first_name=tg_user.first_name,
                          last_name=tg_user.last_name,
                          full_name=tg_user.full_name,
                          telegram_id=tg_user.id)
    await open_user_main_menu(message, config)


async def user_bank_carousel(cq: types.CallbackQuery, db: Database, config, callback_data):
    cur_page = int(callback_data["c_p"])
    act = callback_data["act"]
    amount_of_pages = await db.count_amount_of_bank_pages()
    if act == "next_pg":
        cur_page += 1
    elif act == "prev_pg":
        cur_page -= 1

    if cur_page < 1:
        cur_page = amount_of_pages
    if cur_page > amount_of_pages:
        cur_page = 1
    bank = await db.select_bank_offset(offset=cur_page)
    if not bank:
        return
    bank_text = await format_bank_text(bank_name=bank["bank_name"], bank_desc=bank["bank_description"])
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=bank,
                                                        cur_page=cur_page, amount_of_pages=amount_of_pages,
                                                        for_role="user")
    await cq.message.answer_photo(photo=bank["bank_photo"], caption=bank_text,
                                  reply_markup=reply_markup)


async def user_add_bank_favorites(cq: types.CallbackQuery, db: Database, callback_data):
    bank_id = int(callback_data["bid"])
    cur_page = int(callback_data["c_p"])
    amount_of_pages = await db.count_amount_of_bank_pages()
    bank = await db.select_bank_by_id(bank_id=bank_id)
    if not bank:
        await cq.message.delete_reply_markup()
        await cq.message.answer("Данный займ не был найден в базе данных, похоже он был удалён")
        return
    result = await db.user_add_or_delete_bank_to_favorites(telegram_id=cq.from_user.id, bank_id=bank_id)
    if result:
        status = result.get("status")
    else:
        status = None
    bank_text = await format_bank_text(bank_name=bank["bank_name"], bank_desc=bank["bank_description"])
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=bank,
                                                        cur_page=cur_page, amount_of_pages=amount_of_pages,
                                                        for_role="user",
                                                        bank_status=status)
    try:
        await cq.message.edit_media(InputMedia(media=bank["bank_photo"], caption=bank_text),
                                    reply_markup=reply_markup)
    except:
        pass

def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_callback_query_handler(user_main_menu, act_callback.filter(act="back_to_main_menu"), state="*")
    dp.register_callback_query_handler(user_bank_carousel, bank_navg.filter(menu="bank_preview"),
                                       state="*")
    dp.register_callback_query_handler(user_add_bank_favorites,
                                       bank_inter.filter(act=["add_fav", "del_fav"], menu="bank_preview"),
                                       state="*")
