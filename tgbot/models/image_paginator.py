from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.keyboards.callback_datas import bank_navg, adm_bank_navg, act_callback, adm_act_callback, bank_inter


class ImagePaginator:
    @classmethod
    async def create_keyboard(cls, cur_bank, cur_page, amount_of_pages, for_role="user", bank_status=None):
        if for_role == "admin":
            reply_markup = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                [InlineKeyboardButton(text="Изменить описание")],
                [InlineKeyboardButton(text="Изменить название")],
                [InlineKeyboardButton(text="Изменить фото")],
                [InlineKeyboardButton(text="Изменить ссылку")],
                [
                    InlineKeyboardButton(text="⬅️", callback_data=adm_bank_navg.new(
                        act="prev_pg",
                        c_p=cur_page,
                        menu="bank_preview"
                    )),
                    InlineKeyboardButton(text=f"{cur_page}/{amount_of_pages}", callback_data=adm_bank_navg.new(
                        act="page_info",
                        c_p=cur_page,
                        menu="bank_preview"
                    )),
                    InlineKeyboardButton(text="➡️", callback_data=adm_bank_navg.new(
                        act="next_pg",
                        c_p=cur_page,
                        menu="bank_preview"
                    ))
                ]
            ])
            reply_markup.add(InlineKeyboardButton(text="Главное меню",
                                                  callback_data=adm_act_callback.new(
                                                      act="back_to_main_menu"
                                                  )))
        else:
            if bank_status == 1:
                favorite_button = InlineKeyboardButton(text="Убрать из избранного",
                                                       callback_data=bank_inter.new(
                                                           act="del_fav",
                                                           bid=cur_bank["bank_id"],
                                                           c_p=cur_page,
                                                           menu="bank_preview"
                                                       ))
            else:
                favorite_button = InlineKeyboardButton(text="Добавить в избранное",
                                                       callback_data=bank_inter.new(
                                                           act="add_fav",
                                                           bid=cur_bank["bank_id"],
                                                           c_p=cur_page,
                                                           menu="bank_preview"
                                                       ))
            reply_markup = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                [favorite_button],
                [
                    InlineKeyboardButton(text="⬅️", callback_data=bank_navg.new(
                        act="prev_pg",
                        c_p=cur_page,
                        menu="bank_preview"
                    )),
                    InlineKeyboardButton(text=f"{cur_page}/{amount_of_pages}", callback_data=bank_navg.new(
                        act="page_info",
                        c_p=cur_page,
                        menu="bank_preview"
                    )),
                    InlineKeyboardButton(text="➡️", callback_data=bank_navg.new(
                        act="next_pg",
                        c_p=cur_page,
                        menu="bank_preview"
                    ))
                ]
            ])
            reply_markup.add(InlineKeyboardButton(text="Главное меню",
                                                  callback_data=act_callback.new(act="back_to_main_menu")))

        return reply_markup
