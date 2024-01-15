from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.keyboards.callback_datas import bank_navg, adm_bank_navg, act_callback, adm_act_callback, bank_inter, \
    admbank_inter


class ImagePaginator:
    @classmethod
    async def create_keyboard(cls, cur_bank, cur_page, amount_of_pages, for_role="user", menu="bank_preview"):
        if not cur_bank:
            return
        if for_role == "admin":
            reply_markup = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                [InlineKeyboardButton(text="Изменить описание",
                                      callback_data=admbank_inter.new(
                                          act="adm_chng_desc",
                                          bid=cur_bank["bank_id"],
                                          c_p=cur_page,
                                          menu=menu
                                      ))],
                [InlineKeyboardButton(text="Изменить название",
                                      callback_data=admbank_inter.new(
                                          act="adm_chng_name",
                                          bid=cur_bank["bank_id"],
                                          c_p=cur_page,
                                          menu=menu
                                      ))],
                [InlineKeyboardButton(text="Изменить фото",
                                      callback_data=admbank_inter.new(
                                          act="adm_chng_photo",
                                          bid=cur_bank["bank_id"],
                                          c_p=cur_page,
                                          menu=menu
                                      ))],
                [InlineKeyboardButton(text="Изменить ссылку",
                                      callback_data=admbank_inter.new(
                                          act="adm_chng_url",
                                          bid=cur_bank["bank_id"],
                                          c_p=cur_page,
                                          menu=menu
                                      ))],
                [
                    InlineKeyboardButton(text="⬅️", callback_data=adm_bank_navg.new(
                        act="prev_pg",
                        c_p=cur_page,
                        menu=menu
                    )),
                    InlineKeyboardButton(text=f"{cur_page}/{amount_of_pages}", callback_data=adm_bank_navg.new(
                        act="page_info",
                        c_p=cur_page,
                        menu=menu
                    )),
                    InlineKeyboardButton(text="➡️", callback_data=adm_bank_navg.new(
                        act="next_pg",
                        c_p=cur_page,
                        menu=menu
                    ))
                ]
            ])
            reply_markup.add(InlineKeyboardButton(text="Главное меню",
                                                  callback_data=adm_act_callback.new(
                                                      act="back_to_main_menu"
                                                  )))
        else:
            if cur_bank.get("fav_status"):
                favorite_button = InlineKeyboardButton(text="❌ Убрать из избранного",
                                                       callback_data=bank_inter.new(
                                                           act="del_fav",
                                                           bid=cur_bank["bank_id"],
                                                           c_p=cur_page,
                                                           menu=menu
                                                       ))
            else:
                favorite_button = InlineKeyboardButton(text="✅ Добавить в избранное",
                                                       callback_data=bank_inter.new(
                                                           act="add_fav",
                                                           bid=cur_bank["bank_id"],
                                                           c_p=cur_page,
                                                           menu=menu
                                                       ))
            if cur_bank.get("tag_status"):
                tag_button = InlineKeyboardButton(text="❌ Убрать отметку",
                                                       callback_data=bank_inter.new(
                                                           act="del_tag",
                                                           bid=cur_bank["bank_id"],
                                                           c_p=cur_page,
                                                           menu=menu
                                                       ))
            else:
                tag_button = InlineKeyboardButton(text="🔷 Отметить",
                                                       callback_data=bank_inter.new(
                                                           act="add_tag",
                                                           bid=cur_bank["bank_id"],
                                                           c_p=cur_page,
                                                           menu=menu
                                                       ))

            reply_markup = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                [favorite_button],
                [tag_button],
                [
                    InlineKeyboardButton(text="⬅️", callback_data=bank_navg.new(
                        act="prev_pg",
                        c_p=cur_page,
                        menu=menu
                    )),
                    InlineKeyboardButton(text=f"{cur_page}/{amount_of_pages}", callback_data=bank_navg.new(
                        act="page_info",
                        c_p=cur_page,
                        menu=menu
                    )),
                    InlineKeyboardButton(text="➡️", callback_data=bank_navg.new(
                        act="next_pg",
                        c_p=cur_page,
                        menu=menu
                    ))
                ]
            ])
            reply_markup.add(InlineKeyboardButton(text="Главное меню",
                                                  callback_data=act_callback.new(act="back_to_main_menu")))

        return reply_markup
