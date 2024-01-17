from typing import Union

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ContentType, InputMedia
import aiogram.utils.markdown as fmt
from aiogram.dispatcher.filters import Command

from tgbot.config import Config
from tgbot.keyboards.callback_datas import adm_act_callback, adm_bank_navg, bank_inter
from tgbot.misc.exceptions import ActException, StateException
from tgbot.misc.misc_functions import format_channel_link, format_bank_text, smart_message_interaction_photo
from tgbot.misc.states import AdminStates
from tgbot.models import image_paginator
from tgbot.models.channel_interactions import ChannelInteractions
from tgbot.models.image_paginator import ImagePaginator
from tgbot.models.postgresql import Database
from tgbot.models.users_notification import UsersNotificator


async def open_admin_main_menu(target: Union[types.CallbackQuery, types.Message], config: Config):
    channel_url = await format_channel_link(config.tg_bot.channel_tag)
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить новый банк",
                              callback_data=adm_act_callback.new(act="add_new_bank"))],
        [InlineKeyboardButton(text="Бесплатные займы",
                              callback_data=adm_bank_navg.new(act="adm_bank_carousel",
                                                              c_p="1",
                                                              menu="bank_preview"))],
        [InlineKeyboardButton(text="Все займы", url=channel_url)],
    ])
    if config.misc.main_photo:
        if isinstance(target, types.CallbackQuery):
            if target.message.content_type == ContentType.TEXT:
                await target.message.answer_photo(
                    photo=config.misc.main_photo,
                    caption=f"Привет, {target.from_user.full_name}!\n"
                            f"Для взаимодействия используйте кнопки снизу 👇",
                    reply_markup=reply_markup)
            else:
                await target.message.edit_media(media=InputMedia(
                    media=config.misc.main_photo,
                    caption=
                    f"Привет, {target.from_user.full_name}!\n"
                    f"Для взаимодействия используйте кнопки снизу 👇"),
                    reply_markup=reply_markup)

        elif isinstance(target, types.Message):
            await target.answer_photo(photo=config.misc.main_photo,
                                      caption=f"Привет, {target.from_user.full_name}!\n"
                                              f"Для взаимодействия используйте кнопки снизу 👇",
                                      reply_markup=reply_markup
                                      )
        else:
            print(f"Новый type попал в объект main menu target = {target}")
    else:
        if isinstance(target, types.CallbackQuery):
            if target.message.content_type == ContentType.TEXT:
                await target.message.edit_text(text=f"Привет, {target.from_user.full_name}!\n"
                                                    f"Для взаимодействия используйте кнопки снизу 👇",
                                               reply_markup=reply_markup)
            else:
                await target.message.answer(text=f"Привет, {target.from_user.full_name}!\n"
                                                 f"Для взаимодействия используйте кнопки снизу 👇",
                                            reply_markup=reply_markup)
        else:
            await target.answer(text=f"Привет, {target.from_user.full_name}!\n"
                                     f"Для взаимодействия используйте кнопки снизу 👇",
                                reply_markup=reply_markup)


async def admin_main_menu(cq: types.CallbackQuery, state, config):
    await state.reset_state()
    await open_admin_main_menu(cq, config)


async def admin_start(message: Message, config: Config, state):
    await state.reset_state()
    await open_admin_main_menu(message, config)


async def get_my_id(message: types.Message):
    await message.answer(text=f"Ваш айди телеграм: {fmt.hbold(message.from_user.id)}")


async def get_current_chat(message):
    await message.answer(text=f"Текущий чат: {fmt.hbold(message.chat.id)}")


async def add_new_bank(cq: types.CallbackQuery):
    await AdminStates.waiting_bank_name.set()
    back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Главное меню",
                              callback_data=adm_act_callback.new(act="back_to_main_menu"))]])
    await cq.message.answer(text="Введите название банка", reply_markup=back_to_main_menu)


async def get_bank_name(message: types.Message, state):
    if len(message.html_text) > 120:
        await message.answer("Название слишком длинное")
        return
    await AdminStates.waiting_bank_description.set()
    await state.update_data(bank_name=message.html_text)
    back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Главное меню",
                              callback_data=adm_act_callback.new(act="back_to_main_menu"))]])
    await message.answer(text="Введите описание банка", reply_markup=back_to_main_menu)


async def get_bank_description(message: types.Message, state):
    if len(message.html_text) > 800:
        await message.answer("Описание слишком длинное")
        return
    await AdminStates.waiting_bank_url.set()
    await state.update_data(bank_desc=message.html_text)
    back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Главное меню",
                              callback_data=adm_act_callback.new(act="back_to_main_menu"))]])
    await message.answer(text="Отправьте ссылку на банк",
                         reply_markup=back_to_main_menu)


async def get_bank_url(message: types.Message, state):
    if len(message.text) > 256:
        await message.answer("Url слишком длинный")
        return
    await AdminStates.waiting_bank_photo.set()
    await state.update_data(bank_url=message.text)
    back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Главное меню",
                              callback_data=adm_act_callback.new(act="back_to_main_menu"))]])
    await message.answer(text="Отправьте фото-превью банка",
                         reply_markup=back_to_main_menu)


async def get_bank_photo(message: types.Message, state):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    data = await state.get_data()
    bank_name = data["bank_name"]
    bank_desc = data["bank_desc"]
    bank_url = data["bank_url"]
    message_text = f"{bank_name}\n" \
                   f"{bank_desc}"
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Забрать прямо сейчас!",
                              url=bank_url)],
        [InlineKeyboardButton(text="✅ Подтвердить",
                              callback_data=adm_act_callback.new(act="confirm_creation"))],
        [InlineKeyboardButton(text="❌ Главное меню",
                              callback_data=adm_act_callback.new(act="back_to_main_menu"))]])
    await message.answer_photo(photo=photo_file_id,
                               caption=message_text,
                               reply_markup=reply_markup)


async def adm_confirm_bank_creation(cq: types.CallbackQuery, db: Database, state, config: Config):
    await state.reset_state(with_data=False)
    back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Главное меню",
                              callback_data=adm_act_callback.new(act="back_to_main_menu"))]])
    data = await state.get_data()
    await state.reset_state()

    bank = await db.add_bank(
                            bank_name=data["bank_name"],
                            bank_description=data["bank_desc"],
                            bank_photo=data["photo_file_id"],
                            bank_url=data["bank_url"])
    bank_rating = await db.calculate_bank_rating(bank_id=bank["bank_id"])
    # generating notification message for users
    for channel in config.tg_bot.channels:
        await ChannelInteractions.add_bank_to_channel(bot=cq.bot,
                                                      bank_id=bank["bank_id"],
                                                      db=db,
                                                      channel_id=channel,
                                                      bot_tag=config.tg_bot.bot_name)

    bank_text = await format_bank_text(bank, bank_rating=bank_rating, is_notification=True)
    cur_page = await db.calculate_offset_of_bank(bank_id=bank["bank_id"])
    amount_of_banks = await db.count_amount_of_bank_pages()
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=bank,
                                                        cur_page=cur_page,
                                                        amount_of_pages=amount_of_banks,
                                                        for_role="user",
                                                        menu="bank_preview")
    await cq.message.edit_caption(caption="Банк был успешно создан!", reply_markup=back_to_main_menu)
    msg_to_send = await cq.message.answer_photo(caption=bank_text, photo=bank["bank_photo"],
                                                reply_markup=reply_markup)
    users = await db.select_all_users()
    await UsersNotificator.send_smart_message_to_user(message=msg_to_send, users=users)


async def get_unknown_content(message):
    back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Главное меню",
                              callback_data=adm_act_callback.new(act="back_to_main_menu"))]])
    await message.answer("Похоже было получено то, чего не ожидалось, пожалуйста, отправляйте только то, что я попрошу",
                         reply_markup=back_to_main_menu)


async def adm_bank_carousel(cq: types.CallbackQuery, db: Database, config, callback_data):
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

    bank = await db.select_bank_offset(telegram_id=cq.from_user.id, offset=cur_page)
    if not bank:
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Главное меню",
                                  callback_data=adm_act_callback.new(act="back_to_main_menu"))]])
        try:
            await cq.message.edit_text(text="Список пуст, попробуйте что-нибудь сюда добавить 👍",
                                       reply_markup=reply_markup)
        except:
            try:
                await cq.message.edit_caption(caption="Список пуст, попробуйте что-нибудь сюда добавить 👍",
                                              reply_markup=reply_markup)
            except:
                pass


        return
    bank_rating = await db.calculate_bank_rating(bank["bank_id"])
    bank_text = await format_bank_text(bank=bank, bank_rating=bank_rating)
    reply_markup = await ImagePaginator.create_keyboard(cur_bank=bank,
                                                        cur_page=cur_page, amount_of_pages=amount_of_pages,
                                                        for_role="admin")
    await smart_message_interaction_photo(target=cq,
                                          reply_markup=reply_markup,
                                          msg_text=bank_text,
                                          media_file_id=bank["bank_photo"])


async def adm_change_bank_menu(cq, state, callback_data, db):
    await AdminStates.adm_chng_dest.set()
    bank_id = int(callback_data["bid"])
    act = callback_data["act"]
    await state.update_data(bank_id=bank_id, act=act)
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Главное меню",
                              callback_data=adm_act_callback.new(act="back_to_main_menu"))]
    ])

    if act == "adm_chng_name":
        await AdminStates.adm_chng_name.set()
        await cq.message.answer(text="Введите новое название для банка",
                                reply_markup=reply_markup)
    elif act == "adm_chng_photo":
        await AdminStates.adm_chng_photo.set()
        await cq.message.answer(text="Отправьте новое фото для банка",
                                reply_markup=reply_markup)
    elif act == "adm_chng_url":
        await AdminStates.adm_chng_url.set()
        await cq.message.answer(text="Отправьте новый url для банка",
                                reply_markup=reply_markup)
    elif act == "adm_chng_desc":
        await AdminStates.adm_chng_dest.set()
        await cq.message.answer(text="Отправьте новое описание для банка",
                                reply_markup=reply_markup)
    else:
        raise ActException


async def adm_get_data_for_bank_menu(message: types.Message, state: FSMContext, db: Database):
    cur_state = await state.get_state()
    if cur_state == AdminStates.adm_chng_name.state and message.content_type == ContentType.TEXT:
        bank_name = message.html_text
        await state.update_data(bank_name=bank_name)
    elif cur_state == AdminStates.adm_chng_photo.state and message.content_type == ContentType.PHOTO:
        bank_photo = message.photo
        await state.update_data(bank_photo=bank_photo)
    elif cur_state == AdminStates.adm_chng_url.state and message.content_type == ContentType.TEXT:
        bank_url = message.text
        await state.update_data(bank_url=bank_url)
    elif cur_state == AdminStates.adm_chng_dest.state and message.content_type == ContentType.TEXT:
        bank_description = message.html_text
        await state.update_data(bank_description=bank_description)
    else:
        raise StateException
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить",
                              callback_data=adm_act_callback.new(act="confirm_change"))],
        [InlineKeyboardButton(text="❌ Главное меню",
                              callback_data=adm_act_callback.new(act="back_to_main_menu"))]])
    await message.answer(text=message.text, reply_markup=reply_markup)


async def confirm_change(cq, callback_data, db: Database, state: FSMContext):
    await state.reset_state(with_data=False)
    data = await state.get_data()
    await state.reset_state()
    act = data["act"]
    bank_id = int(data["bank_id"])
    if act == "adm_chng_name":
        await db.update_bank_menu(bank_id, data)
    elif act == "adm_chng_photo":
        await db.update_bank_menu(bank_id, data)
    elif act == "adm_chng_url":
        await db.update_bank_menu(bank_id, data)
    elif act == "adm_chng_desc":
        await db.update_bank_menu(bank_id, data)
    else:
        raise ActException
    await cq.message.edit_text("Выполнено успешно!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Главное меню",
                              callback_data=adm_act_callback.new(act="back_to_main_menu"))]
    ]))


def register_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, commands=["admin"], state="*",
                                is_admin=True)
    dp.register_callback_query_handler(admin_main_menu, adm_act_callback.filter(act="back_to_main_menu"), state="*",
                                       is_admin=True)
    dp.register_message_handler(get_my_id, commands=["get_my_id"], state="*")
    dp.register_channel_post_handler(get_current_chat, Command("get_current_chat"), state="*")
    dp.register_callback_query_handler(add_new_bank, adm_act_callback.filter(act="add_new_bank"), state="*",
                                       is_admin=True)
    dp.register_message_handler(get_bank_name, state=AdminStates.waiting_bank_name,
                                content_types=ContentType.TEXT,
                                is_admin=True)
    dp.register_message_handler(get_bank_description, state=AdminStates.waiting_bank_description,
                                content_types=ContentType.TEXT,
                                is_admin=True)
    dp.register_message_handler(get_bank_url, state=AdminStates.waiting_bank_url,
                                content_types=ContentType.TEXT,
                                is_admin=True)
    dp.register_message_handler(get_bank_photo, state=AdminStates.waiting_bank_photo,
                                content_types=ContentType.PHOTO,
                                is_admin=True)
    dp.register_message_handler(get_unknown_content, state=[AdminStates.waiting_bank_name,
                                                            AdminStates.waiting_bank_description,
                                                            AdminStates.waiting_bank_photo],
                                content_types=ContentType.ANY,
                                is_admin=True)
    dp.register_callback_query_handler(adm_confirm_bank_creation, adm_act_callback.filter(act="confirm_creation"),
                                       state=AdminStates.waiting_bank_photo,
                                       is_admin=True)
    dp.register_callback_query_handler(adm_bank_carousel, adm_bank_navg.filter(menu="bank_preview"),
                                       state="*",
                                       is_admin=True)
    dp.register_message_handler(adm_get_data_for_bank_menu,
                                state=[AdminStates.adm_chng_name,
                                       AdminStates.adm_chng_photo,
                                       AdminStates.adm_chng_url,
                                       AdminStates.adm_chng_dest])
    dp.register_callback_query_handler(adm_change_bank_menu,
                                       bank_inter.filter(act=[
                                           "adm_chng_name",
                                           "adm_chng_photo",
                                           "adm_chng_url",
                                           "adm_chng_desc"]
                                       ), state="*", is_admin=True)
    dp.register_callback_query_handler(confirm_change, adm_act_callback.filter(act="confirm_change"),
                                       is_admin=True, state=[AdminStates.adm_chng_name,
                                       AdminStates.adm_chng_photo,
                                       AdminStates.adm_chng_url,
                                       AdminStates.adm_chng_dest])
