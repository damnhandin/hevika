from aiogram.dispatcher.filters.state import StatesGroup, State


class AdminStates(StatesGroup):
    waiting_bank_name = State()
    waiting_bank_description = State()
    waiting_bank_url = State()
    waiting_bank_photo = State()
    adm_chng_name = State()
    adm_chng_photo = State()
    adm_chng_url = State()
    adm_chng_dest = State()
