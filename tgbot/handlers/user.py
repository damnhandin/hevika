from typing import Union

from aiogram import Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.config import Config
from tgbot.keyboards.callback_datas import bank_navg, bank_inter, act_callback
from tgbot.misc.misc_functions import format_channel_link, format_bank_text, smart_message_interaction_photo, \
    select_func_and_count_banks
from tgbot.models.image_paginator import ImagePaginator
from tgbot.models.postgresql import Database


async def open_user_main_menu(target: Union[types.CallbackQuery, types.Message], config: Config):
    link = await format_channel_link(config.tg_bot.channel_tag)
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Бесплатные займы 💲",
                              callback_data=bank_navg.new(
                                  act="user_bank_carousel",
                                  menu="bank_preview",
                                  c_p="1"))],
        [InlineKeyboardButton(text="Избранное ❇️",
                              callback_data=act_callback.new(
                                  act="us_open_fav"))],
        [InlineKeyboardButton(text="Отмеченные 🔷",
                              callback_data=act_callback.new(
                                  act="us_open_tagged"))],
        [InlineKeyboardButton(text="Показать все бесплатные займы",
                              url=link)]
    ])
    text = f"Приветствую тебя, {target.from_user.full_name}! 👋\n"\
           f"Я помогу тебе найти беспроцентные займы в пару кликов! 😉"\
           "Для взаимодействия используй кнопки снизу 👇"
    await smart_message_interaction_photo(target=target, msg_text=text, reply_markup=reply_markup,
                                          media_file_id=config.misc.main_photo)


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


async def user_bank_carousel(cq: types.CallbackQuery, db: Database, callback_data):

    cur_page = int(callback_data["c_p"])
    act = callback_data["act"]
    if act == "next_pg":
        cur_page += 1
    elif act == "prev_pg":
        cur_page -= 1
    menu = callback_data["menu"]
    bank_func, amount_of_pages = await select_func_and_count_banks(menu, db, cq.from_user.id)
    if cur_page < 1:
        cur_page = amount_of_pages
    if cur_page > amount_of_pages:
        cur_page = 1
    bank = await bank_func(telegram_id=cq.from_user.id, offset=cur_page)
    if not bank:
        return
    bank_text = await format_bank_text(bank=bank)
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=bank,
                                                        cur_page=cur_page, amount_of_pages=amount_of_pages,
                                                        for_role="user",
                                                        menu=menu)
    await smart_message_interaction_photo(target=cq, msg_text=bank_text, reply_markup=reply_markup,
                                          media_file_id=bank["bank_photo"])


async def user_add_bank_favorites(cq: types.CallbackQuery, db: Database, callback_data):
    bank_id = int(callback_data["bid"])
    cur_page = int(callback_data["c_p"])
    menu = callback_data["manu"]
    status = True if callback_data.get("act") == "add_fav" else False
    bank = await db.user_edit_user_bank_status(telegram_id=cq.from_user.id, bank_id=bank_id, status_str="fav_status",
                                               status=status)
    if not bank:
        await cq.message.delete_reply_markup()
        await cq.message.answer("Данный займ не был найден в базе данных, похоже он был удалён")
        return

    bank_func, amount_of_pages = await select_func_and_count_banks(menu, db, cq.from_user.id)
    if cur_page > amount_of_pages:
        cur_page = 1
    elif cur_page < 1:
        cur_page = amount_of_pages
    bank = await bank_func(telegram_id=cq.from_user.id, offset=cur_page)
    bank_text = await format_bank_text(bank=bank)
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=bank,
                                                        cur_page=cur_page, amount_of_pages=amount_of_pages,
                                                        for_role="user")

    await smart_message_interaction_photo(target=cq, reply_markup=reply_markup, msg_text=bank_text,
                                          media_file_id=bank.get("bank_photo"))


async def user_add_del_tag_bank(cq, db, callback_data):
    bank_id = int(callback_data["bid"])
    cur_page = int(callback_data["c_p"])
    menu = callback_data["menu"]
    status = True if callback_data.get("act") == "add_tag" else False
    bank = await db.user_edit_user_bank_status(telegram_id=cq.from_user.id, bank_id=bank_id, status_str="tag_status",
                                               status=status)
    if not bank:
        await cq.message.delete_reply_markup()
        await cq.message.answer("Данный займ не был найден в базе данных, похоже он был удалён")
        return
    bank_func, amount_of_pages = await select_func_and_count_banks(menu, db, cq.from_user.id)
    if cur_page > amount_of_pages:
        cur_page = 1
    elif cur_page < 1:
        cur_page = amount_of_pages
    bank = await bank_func(telegram_id=cq.from_user.id, offset=cur_page)
    bank_text = await format_bank_text(bank=bank)
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=bank,
                                                        cur_page=cur_page, amount_of_pages=amount_of_pages,
                                                        for_role="user")
    await smart_message_interaction_photo(target=cq, reply_markup=reply_markup, msg_text=bank_text,
                                          media_file_id=bank.get("bank_photo"))


async def us_open_fav(cq, db: Database):
    count_user_banks = await db.count_amount_of_user_banks_fav(user_tg_id=cq.from_user.id)
    if not count_user_banks or count_user_banks == 0:
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Главное меню",
                                  callback_data=act_callback.new(act="back_to_main_menu"))]
        ])
        await cq.message.answer("Список пуст, попробуйте что-нибудь сюда добавить 👍",
                                reply_markup=reply_markup)
        return
    cur_bank = await db.select_user_fav_bank(telegram_id=cq.from_user.id)
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=cur_bank, cur_page=1, amount_of_pages=count_user_banks,
                                                        for_role="user", menu="favorites")
    msg_text = "Для взаимодействия используйте кнопки снизу 👇"
    await smart_message_interaction_photo(target=cq, reply_markup=reply_markup, msg_text=msg_text,
                                          media_file_id=cur_bank.get("bank_photo"))


async def us_open_tagged(cq, db: Database):
    count_user_banks = await db.count_amount_of_user_banks_tag(user_tg_id=cq.from_user.id)
    if not count_user_banks or count_user_banks == 0:
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Главное меню",
                                  callback_data=act_callback.new(act="back_to_main_menu"))]
        ])
        await cq.message.answer("Список пуст, попробуйте что-нибудь сюда добавить 👍",
                                reply_markup=reply_markup)
        return
    cur_bank = await db.select_user_tag_bank(telegram_id=cq.from_user.id)
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=cur_bank, cur_page=1, amount_of_pages=count_user_banks,
                                                        for_role="user", menu="tagged")
    msg_text = "Для взаимодействия используйте кнопки снизу 👇"
    await smart_message_interaction_photo(target=cq, reply_markup=reply_markup, msg_text=msg_text,
                                          media_file_id=cur_bank.get("bank_photo"))


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_callback_query_handler(user_main_menu, act_callback.filter(act="back_to_main_menu"), state="*")
    dp.register_callback_query_handler(user_bank_carousel, bank_navg.filter(
        menu=["bank_preview", "favorites", "tagged"]),
                                       state="*")
    dp.register_callback_query_handler(user_add_bank_favorites,
                                       bank_inter.filter(act=["add_fav", "del_fav"], menu="bank_preview"),
                                       state="*")
    dp.register_callback_query_handler(user_add_del_tag_bank,
                                       bank_inter.filter(act=["add_tag", "del_tag"], menu="bank_preview"),
                                       state="*")
    dp.register_callback_query_handler(us_open_fav, act_callback.filter(act="us_open_fav"),
                                       state="*")
    dp.register_callback_query_handler(us_open_tagged, act_callback.filter(act="us_open_tagged"),
                                       state="*")
