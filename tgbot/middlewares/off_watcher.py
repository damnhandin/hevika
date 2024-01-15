from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware


class OffWatchesMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def on_post_process_callback_query(self, cq: types.CallbackQuery, data, *args, **kwargs):
        try:
            await cq.answer()
        except:
            pass
