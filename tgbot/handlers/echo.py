from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext


async def bot_echo_all(message: types.Message, state: FSMContext):
    await message.answer("Прохоже, что что-то пошло не так, "
                         "для взаимодействие с ботом нажми или напиши команду 👉 /start")


def register_echo(dp: Dispatcher):
    dp.register_message_handler(bot_echo_all, state="*", content_types=types.ContentTypes.ANY)
