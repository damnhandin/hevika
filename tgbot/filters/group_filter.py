import typing

from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import ChatType


class GroupFilter(BoundFilter):
    key = 'is_group'

    def __init__(self, is_group: typing.Optional[bool] = None):
        self.is_group = is_group

    async def check(self, obj):
        if not obj:
            return True
        if self.is_group is None:
            return False
        try:
            return (obj.chat.type != ChatType.PRIVATE) == self.is_group
        except:
            return True
