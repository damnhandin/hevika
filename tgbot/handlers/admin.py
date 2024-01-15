from typing import Union

from aiogram import Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ContentType, InputMedia
import aiogram.utils.markdown as fmt
from aiogram.dispatcher.filters import Command

from tgbot.config import Config
from tgbot.keyboards.callback_datas import adm_act_callback, adm_bank_navg
from tgbot.misc.misc_functions import format_channel_link, format_bank_text, smart_message_interaction_photo
from tgbot.misc.states import AdminStates
from tgbot.models.channel_interactions import ChannelInteractions
from tgbot.models.image_paginator import ImagePaginator
from tgbot.models.postgresql import Database


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
    if isinstance(target, types.CallbackQuery):
        if target.message.content_type == ContentType.TEXT:
            await target.message.answer_photo(
                photo=config.misc.main_photo,
                caption=f"Привет, {target.from_user.full_name}!\n"
                        f"Для взаимодействия используй кнопки снизу 👇",
                reply_markup=reply_markup)
        else:
            await target.message.edit_media(media=InputMedia(media=config.misc.main_photo,
                                                             caption=f"Привет, {target.from_user.full_name}!\n"
                                                                     f"Для взаимодействия используй кнопки снизу 👇"),
                                            reply_markup=reply_markup)

    elif isinstance(target, types.Message):
        await target.answer_photo(photo=config.misc.main_photo,
                                  caption=f"Привет, {target.from_user.full_name}!\n"
                                          f"Для взаимодействия используй кнопки снизу 👇",
                                  reply_markup=reply_markup
                                  )
    else:
        print(f"Новый type попал в объект main menu target = {target}")


async def admin_main_menu(cq: types.CallbackQuery, config):
    await open_admin_main_menu(cq, config)


async def admin_start(message: Message, config: Config):
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
    for channel in config.tg_bot.channels:
        await ChannelInteractions.add_bank_to_channel(bot=cq.bot,
                                                      bank_id=bank["bank_id"],
                                                      db=db,
                                                      channel_id=channel,
                                                      bot_tag=config.tg_bot.bot_name)
    await cq.message.edit_caption(caption="Банк был успешно создан!", reply_markup=back_to_main_menu)


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


def register_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, commands=["admin"], state="*",
                                is_admin=True)
    dp.register_callback_query_handler(admin_main_menu, adm_act_callback.filter(act="back_to_main_menu"), state="*",
                                       is_admin=True)
    dp.register_message_handler(get_my_id, commands=["get_my_id"], state="*",
                                is_admin=True)
    dp.register_channel_post_handler(get_current_chat, Command("get_current_chat"), state="*",
                                     is_admin=True)
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
