from aiogram import types


class UsersNotificator:
    @classmethod
    async def send_smart_message_to_user(cls, message: types.Message, users):
        for user in users:
            try:
                await message.send_copy(chat_id=user["telegram_id"])
            except:
                pass