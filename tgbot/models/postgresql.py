import contextlib
from datetime import datetime
from typing import Optional, AsyncIterator

import asyncpg

from tgbot.config import Config


class Database:
    def __init__(self, config: Config):
        self._pool: Optional[asyncpg.Pool] = None
        self.config: Config = config

    async def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(32) NULL,
            first_name VARCHAR(64) NOT NULL,
            last_name VARCHAR(64) NULL,
            full_name VARCHAR(128) NOT NULL,
            registration_date DATE NOT NULL,
            telegram_id BIGINT NOT NULL UNIQUE
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_banks(self):
        sql = """
        CREATE TABLE IF NOT EXISTS banks (
        bank_name VARCHAR(120) NOT NULL, 
        bank_description VARCHAR(255) NOT NULL, 
        bank_photo VARCHAR(128) NOT NULL, 
        bank_url VARCHAR(128) NOT NULL
        );
        """
        await self.execute(sql, execute=True)

    async def select_user_tg_id(self, telegram_id):
        sql = "SELECT * FROM users WHERE telegram_id=$1;"
        return await self.execute(sql, telegram_id, fetchrow=True)

    async def add_user(self, username, first_name, last_name, full_name, telegram_id):
        registration_date = datetime.now()
        sql = """
        INSERT INTO users (username, first_name, last_name, full_name, registration_date, telegram_id) VALUES (
        $1, $2, $3, $4, $5, $6
        );
        """
        await self.execute(sql, username, first_name, last_name, full_name, registration_date, telegram_id,
                           execute=True)

    async def add_bank(self, bank_name, bank_description, bank_photo, bank_url):
        sql = "INSERT INTO banks (bank_name, bank_description, bank_photo, bank_url) VALUES ($1, $2, $3, $4)"
        await self.execute(sql, bank_name, bank_description, bank_photo, bank_url, execute=True)

    async def drop_table_users(self):
        await self.execute("DROP TABLE IF EXISTS users;", execute=True)

    async def drop_table_banks(self):
        await self.execute("DROP TABLE IF EXISTS banks;", execute=True)

    async def execute(self, command, *args,
                      fetch: bool = False,
                      fetchval: bool = False,
                      fetchrow: bool = False,
                      execute: bool = False,
                      isolation=None):
        async with self._transaction(isolation=isolation) as connection:  # type: asyncpg.Connection
            if fetch:
                result = await connection.fetch(command, *args)
            elif fetchval:
                result = await connection.fetchval(command, *args)
            elif fetchrow:
                result = await connection.fetchrow(command, *args)
            elif execute:
                result = await connection.execute(command, *args)
        return result

    # Это для корректной работы с соединениями
    @contextlib.asynccontextmanager
    async def _transaction(self, isolation=None) -> AsyncIterator[asyncpg.Connection]:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                user=self.config.db.user,
                password=self.config.db.password,
                host=self.config.db.host,
                database=self.config.db.database,
            )
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            async with conn.transaction(isolation=isolation):
                yield conn

    async def close(self) -> None:
        if self._pool is None:
            return None

        await self._pool.close()
