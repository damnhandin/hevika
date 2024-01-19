from typing import Union

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.config import Config
from tgbot.keyboards.callback_datas import bank_navg, bank_inter, act_callback, user_rates_cd
from tgbot.misc.misc_functions import format_channel_link, format_bank_text, smart_message_interaction_photo, \
    select_func_and_count_banks
from tgbot.models.image_paginator import ImagePaginator
from tgbot.models.postgresql import Database


async def open_user_main_menu(target: Union[types.CallbackQuery, types.Message], config: Config):
    if config.misc.main_photo:
        main_photo = config.misc.main_photo
    else:
        main_photo = None
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
    text = f"Приветствую вас, {target.from_user.full_name}! 👋\n"\
           f"Я помогу вам найти беспроцентные займы в пару кликов! 😉\n\n"\
           "Для взаимодействия используйте кнопки снизу 👇"
    await smart_message_interaction_photo(target=target, msg_text=text, reply_markup=reply_markup,
                                          media_file_id=main_photo)


async def user_main_menu(cq, config, state, db):
    await state.reset_state()
    user = await db.select_user_tg_id(telegram_id=cq.from_user.id)
    tg_user = cq.from_user
    if not user:
        await db.add_user(username=tg_user.username,
                          first_name=tg_user.first_name,
                          last_name=tg_user.last_name,
                          full_name=tg_user.full_name,
                          telegram_id=tg_user.id)
    await open_user_main_menu(cq, config)


async def user_start(message: Message, db: Database, config: Config, state):
    await state.reset_state()
    user = await db.select_user_tg_id(telegram_id=message.from_user.id)
    tg_user = message.from_user
    if not user:
        await db.add_user(username=tg_user.username,
                          first_name=tg_user.first_name,
                          last_name=tg_user.last_name,
                          full_name=tg_user.full_name,
                          telegram_id=tg_user.id)
    deep_link_args = message.get_args()
    print(deep_link_args)
    bank = None
    try:
        bank_id = int(deep_link_args[2:])
        bank = await db.select_bank_by_id(bank_id=bank_id)
    except:
        pass
    if not bank:
        await open_user_main_menu(message, config)
        return
    bank_rating = await db.calculate_bank_rating(bank_id=bank["bank_id"])
    bank_text = await format_bank_text(bank=bank, bank_rating=bank_rating)
    cur_page = await db.calculate_offset_of_bank(bank_id=bank["bank_id"])
    amount_of_pages = await db.count_amount_of_bank_pages()
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=bank,
                                                        cur_page=cur_page,
                                                        amount_of_pages=amount_of_pages,
                                                        for_role="user",
                                                        menu="bank_preview")
    await smart_message_interaction_photo(target=message, msg_text=bank_text, reply_markup=reply_markup,
                                          media_file_id=bank["bank_photo"])


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
        back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Главное меню",
                                  callback_data=act_callback.new(act="back_to_main_menu"))]
        ])
        await smart_message_interaction_photo(target=cq,
                                              msg_text="Список пуст, попробуйте что-нибудь сюда добавить 👍",
                                              reply_markup=back_to_main_menu,
                                              media_file_id=bank["bank_photo"])
        return
    bank_rating = await db.calculate_bank_rating(bank_id=bank["bank_id"])
    bank_text = await format_bank_text(bank=bank, bank_rating=bank_rating)
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=bank,
                                                        cur_page=cur_page, amount_of_pages=amount_of_pages,
                                                        for_role="user",
                                                        menu=menu)
    await smart_message_interaction_photo(target=cq, msg_text=bank_text, reply_markup=reply_markup,
                                          media_file_id=bank["bank_photo"])


async def user_add_bank_favorites(cq: types.CallbackQuery, db: Database, callback_data):
    bank_id = int(callback_data["bid"])
    cur_page = int(callback_data["c_p"])
    menu = callback_data["menu"]
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
    if not bank:
        back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Главное меню",
                                  callback_data=act_callback.new(act="back_to_main_menu"))]
        ])
        await smart_message_interaction_photo(target=cq,
                                              msg_text="Список пуст, попробуйте что-нибудь сюда добавить 👍",
                                              reply_markup=back_to_main_menu)
        return
    bank_rating = await db.calculate_bank_rating(bank_id=bank["bank_id"])
    bank_text = await format_bank_text(bank=bank, bank_rating=bank_rating)
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=bank,
                                                        cur_page=cur_page, amount_of_pages=amount_of_pages,
                                                        for_role="user",
                                                        menu=menu)

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
    if not bank:
        back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Главное меню",
                                  callback_data=act_callback.new(act="back_to_main_menu"))]
        ])
        await smart_message_interaction_photo(target=cq,
                                              msg_text="Список пуст, попробуйте что-нибудь сюда добавить 👍",
                                              reply_markup=back_to_main_menu)
        return
    bank_rating = await db.calculate_bank_rating(bank_id=bank["bank_id"])
    bank_text = await format_bank_text(bank=bank, bank_rating=bank_rating)
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=bank,
                                                        cur_page=cur_page, amount_of_pages=amount_of_pages,
                                                        for_role="user",
                                                        menu=menu)
    await smart_message_interaction_photo(target=cq, reply_markup=reply_markup, msg_text=bank_text,
                                          media_file_id=bank.get("bank_photo"))


async def us_open_fav(cq, db: Database):
    count_user_banks = await db.count_amount_of_user_banks_fav(user_tg_id=cq.from_user.id)
    back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Главное меню",
                              callback_data=act_callback.new(act="back_to_main_menu"))]
    ])
    if not count_user_banks or count_user_banks == 0:
        await smart_message_interaction_photo(target=cq,
                                              msg_text="Список пуст, попробуйте что-нибудь сюда добавить 👍",
                                              reply_markup=back_to_main_menu)
        return

    cur_bank = await db.select_user_fav_bank(telegram_id=cq.from_user.id)
    if not cur_bank:
        await smart_message_interaction_photo(target=cq,
                                              msg_text="Список пуст, попробуйте что-нибудь сюда добавить 👍",
                                              reply_markup=back_to_main_menu)
        return
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=cur_bank, cur_page=1, amount_of_pages=count_user_banks,
                                                        for_role="user", menu="favorites")
    bank_rating = await db.calculate_bank_rating(bank_id=cur_bank["bank_id"])
    msg_text = await format_bank_text(bank=cur_bank, bank_rating=bank_rating)
    await smart_message_interaction_photo(target=cq, reply_markup=reply_markup, msg_text=msg_text,
                                          media_file_id=cur_bank.get("bank_photo"))


async def us_open_tagged(cq, db: Database):
    count_user_banks = await db.count_amount_of_user_banks_tag(user_tg_id=cq.from_user.id)
    back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Главное меню",
                              callback_data=act_callback.new(act="back_to_main_menu"))]
    ])
    if not count_user_banks or count_user_banks == 0:
        await smart_message_interaction_photo(target=cq,
                                              msg_text="Список пуст, попробуйте что-нибудь сюда добавить 👍",
                                              reply_markup=back_to_main_menu)
        return
    cur_bank = await db.select_user_tag_bank(telegram_id=cq.from_user.id)
    if not cur_bank:
        await smart_message_interaction_photo(target=cq,
                                              msg_text="Список пуст, попробуйте что-нибудь сюда добавить 👍",
                                              reply_markup=back_to_main_menu)
        return

    reply_markup = await ImagePaginator.create_keyboard(cur_bank=cur_bank, cur_page=1, amount_of_pages=count_user_banks,
                                                        for_role="user", menu="tagged")
    bank_rating = await db.calculate_bank_rating(bank_id=cur_bank["bank_id"])
    msg_text = await format_bank_text(bank=cur_bank, bank_rating=bank_rating)
    await smart_message_interaction_photo(target=cq, reply_markup=reply_markup, msg_text=msg_text,
                                          media_file_id=cur_bank.get("bank_photo"))


async def user_start_rate_bank(cq, db: Database, config, callback_data):
    user = await db.select_user_tg_id(telegram_id=cq.from_user.id)
    if not user:
        await open_user_main_menu(target=cq, config=config)
        return
    bank_id = int(callback_data["bid"])
    bank = await db.select_bank_by_id(bank_id=bank_id)
    if not bank:
        await cq.message.delete_reply_markup()
        await cq.message.answer("Данный заем не был найден")
        return
    is_rated = await db.check_if_user_rate_bank(
        telegram_id=cq.from_user.id,
        bank_id=bank_id)
    if is_rated:
        await cq.message.answer("Вы уже поставили оценку на данный заем")
        return

    rating_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data=user_rates_cd.new(bid=bank["bank_id"],
                                                                     ra=1)),
         InlineKeyboardButton(text="2", callback_data=user_rates_cd.new(bid=bank["bank_id"],
                                                                     ra=2)),
         InlineKeyboardButton(text="3", callback_data=user_rates_cd.new(bid=bank["bank_id"],
                                                                     ra=3)),
         InlineKeyboardButton(text="4", callback_data=user_rates_cd.new(bid=bank["bank_id"],
                                                                     ra=4)),
         InlineKeyboardButton(text="5", callback_data=user_rates_cd.new(bid=bank["bank_id"],
                                                                     ra=5))],
        [InlineKeyboardButton(text="Главное меню",
                              callback_data=act_callback.new(act="back_to_main_menu"))]
    ])
    await cq.message.answer(f"Оцените {bank['bank_name']}:", reply_markup=rating_keyboard)


async def user_finish_rate_bank(cq, db, callback_data, config):
    back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Главное меню",
                              callback_data=act_callback.new(act="back_to_main_menu"))]
    ])
    user = await db.select_user_tg_id(telegram_id=cq.from_user.id)
    if not user:
        await open_user_main_menu(target=cq, config=config)
        return
    bank_id = int(callback_data["bid"])
    bank = await db.select_bank_by_id(bank_id=bank_id)
    if not bank:
        await cq.message.delete_reply_markup()
        await cq.message.answer("Данный заем не был найден", reply_markup=back_to_main_menu)
        return
    is_rated = await db.check_if_user_rate_bank(
        telegram_id=cq.from_user.id,
        bank_id=bank_id)
    if is_rated:
        await cq.message.answer("Вы уже поставили оценку на данный заем", reply_markup=back_to_main_menu)
        return

    rate_number = int(callback_data["ra"])
    if rate_number < 0 or rate_number > 5:
        await cq.message.delete_reply_markup()
        await cq.message.answer(text="Произошла ошибка", reply_markup=back_to_main_menu)
        return
    try:
        await db.user_rate_bank(bank_id=bank_id, telegram_id=cq.from_user.id, rate_number=rate_number)
    except Exception as exc:
        await cq.message.answer("Вы уже поставили оценку на данный заем", reply_markup=back_to_main_menu)
        return
    else:
        await cq.message.answer(text=f"Вы успешно поставили оценку {rate_number} ⭐️!!!",
                                reply_markup=back_to_main_menu)
        await cq.message.delete_reply_markup()


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, CommandStart(), state="*")
    dp.register_callback_query_handler(user_main_menu, act_callback.filter(act="back_to_main_menu"), state="*")
    dp.register_callback_query_handler(user_bank_carousel, bank_navg.filter(
        menu=["bank_preview", "favorites", "tagged"]),
                                       state="*")
    dp.register_callback_query_handler(user_add_bank_favorites,
                                       bank_inter.filter(act=["add_fav", "del_fav"]),
                                       state="*")
    dp.register_callback_query_handler(user_add_del_tag_bank,
                                       bank_inter.filter(act=["add_tag", "del_tag"]),
                                       state="*")
    dp.register_callback_query_handler(us_open_fav, act_callback.filter(act="us_open_fav"),
                                       state="*")
    dp.register_callback_query_handler(us_open_tagged, act_callback.filter(act="us_open_tagged"),
                                       state="*")
    dp.register_callback_query_handler(user_start_rate_bank, bank_inter.filter(act="set_rate"), state="*")
    dp.register_callback_query_handler(user_finish_rate_bank, user_rates_cd.filter(), state="*")

