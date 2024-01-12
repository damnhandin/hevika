from aiogram.dispatcher.filters.state import StatesGroup, State


class AdminStates(StatesGroup):
    waiting_bank_name = State()
    waiting_bank_description = State()
    waiting_bank_url = State()
    waiting_bank_photo = State()
