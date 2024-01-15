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
        bank_id SERIAL PRIMARY KEY,
        bank_name VARCHAR(120) NOT NULL, 
        bank_description VARCHAR(800) NOT NULL, 
        bank_photo VARCHAR(128) NOT NULL, 
        bank_url VARCHAR(256) NOT NULL
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_bank_posts(self):
        sql = """
        CREATE TABLE IF NOT EXISTS bank_posts (
        bank_id INT REFERENCES banks(bank_id) ON DELETE NO ACTION ON UPDATE CASCADE,
        channel_id BIGINT NOT NULL,
        post_id BIGINT NOT NULL);
        """
        await self.execute(sql, execute=True)

    async def create_table_user_banks(self):
        sql = """
        CREATE TABLE IF NOT EXISTS user_banks (
        user_telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE NO ACTION ON UPDATE CASCADE,
        bank_id INT REFERENCES banks(bank_id) ON DELETE CASCADE ON UPDATE CASCADE,
        fav_status BOOL NOT NULL,
        tag_status BOOL NOT NULL
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_user_bank_ratings(self):
        sql = """
        CREATE TABLE IF NOT EXISTS user_bank_ratings (
        telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE NO ACTION ON UPDATE CASCADE,
        bank_id INT REFERENCES banks(bank_id) ON DELETE CASCADE ON UPDATE CASCADE,
        rating INT NOT NULL
        );
        """
        await self.execute(sql, execute=True)


    async def add_post_to_bd(self, bank_id, channel_id, post_id):
        sql = "INSERT INTO bank_posts (bank_id, channel_id, post_id) VALUES ($1, $2, $3);"
        await self.execute(sql, bank_id, channel_id, post_id, execute=True)

    async def select_user_fav_bank(self, telegram_id, offset=0):
        offset = offset - 1
        if offset < 0:
            offset = 0
        sql = "SELECT * FROM banks INNER JOIN user_banks USING(bank_id) " \
              "WHERE user_telegram_id=$1 AND fav_status=True OFFSET $2;"
        return await self.execute(sql, telegram_id, offset, fetchrow=True)

    async def count_offset_of_bank(self, bank_id):
        return await self.execute("SELECT COUNT(*) FROM banks WHERE bank_id<$1", bank_id, fetchval=True)

    async def select_user_tag_bank(self, telegram_id, offset=0):
        offset = offset - 1
        if offset < 0:
            offset = 0
        sql = "SELECT * FROM banks INNER JOIN user_banks USING(bank_id) " \
              "WHERE user_telegram_id=$1 AND tag_status=True OFFSET $2;"
        return await self.execute(sql, telegram_id, offset, fetchrow=True)

    async def select_bank_by_id(self, bank_id):
        sql = "SELECT * FROM banks WHERE bank_id=$1;"
        return await self.execute(sql, bank_id, fetchrow=True)

    async def select_user_tg_id(self, telegram_id):
        sql = "SELECT * FROM users WHERE telegram_id=$1;"
        return await self.execute(sql, telegram_id, fetchrow=True)

    async def count_amount_of_bank_pages(self, *args):
        return await self.execute("SELECT COUNT(*) FROM banks", fetchval=True) or 1

    async def count_amount_of_user_banks_fav(self, user_tg_id):
        return await self.execute("SELECT COUNT(*) FROM banks INNER JOIN user_banks USING(bank_id) "
                                  "WHERE user_telegram_id=$1 AND fav_status=True", user_tg_id, fetchval=True) or 1

    async def count_amount_of_user_banks_tag(self, user_tg_id):
        return await self.execute("SELECT COUNT(*) FROM banks INNER JOIN user_banks USING(bank_id) "
                                  "WHERE user_telegram_id=$1 AND tag_status=True", user_tg_id,
                                  fetchval=True) or 1

    async def check_if_user_rate_bank(self, telegram_id, bank_id):
        return await self.execute("SELECT * FROM user_bank_ratings WHERE telegram_id=$1 AND bank_id=$2",
                                  telegram_id, bank_id,
                                  fetchrow=True)

    async def calculate_bank_rating(self, bank_id):
        res = await self.execute("SELECT COUNT(*) as count, SUM(rating) as sum FROM user_bank_ratings "
                                 "WHERE bank_id=$1;", bank_id,
                                 fetchrow=True)
        if res["count"] <= 0 or res["sum"] is None:
            return 0
        return res["sum"] / res["count"]

    async def user_rate_bank(self, bank_id, telegram_id, rate_number):
        async with self._transaction(isolation="serializable") as connection:
            sql = "SELECT * FROM user_bank_ratings WHERE bank_id=$1 AND telegram_id=$2 FOR UPDATE;"
            res = await connection.fetchrow(sql, bank_id, telegram_id)
            if res:
                raise Exception

            sql = "INSERT INTO user_bank_ratings (telegram_id, bank_id, rating) VALUES($1, $2, $3);"
            await connection.execute(sql, telegram_id, bank_id, rate_number)

    async def select_bank_offset(self, telegram_id, offset):
        offset = offset - 1
        if offset < 0:
            offset = 0
        sql = "SELECT banks.*, user_banks.fav_status, user_banks.tag_status FROM banks " \
              "LEFT JOIN user_banks ON user_banks.user_telegram_id=$2 AND banks.bank_id = user_banks.bank_id OFFSET $1"
        return await self.execute(sql, offset, telegram_id, fetchrow=True)

    async def add_user(self, username, first_name, last_name, full_name, telegram_id):
        registration_date = datetime.now()
        sql = """
        INSERT INTO users (username, first_name, last_name, full_name, registration_date, telegram_id) VALUES (
        $1, $2, $3, $4, $5, $6
        );
        """
        await self.execute(sql, username, first_name, last_name, full_name, registration_date, telegram_id,
                           execute=True)

    async def select_user_bank_full(self, telegram_id, bank_id):
        sql = "SELECT banks.*, user_banks.fav_status, user_banks.tag_status FROM banks " \
              "LEFT JOIN user_banks ON banks.bank_id = user_banks.bank_id " \
              "WHERE banks.bank_id=$1 AND user_banks.user_telegram_id=$2;"
        return await self.execute(sql, bank_id, telegram_id, fetchrow=True)

    async def user_edit_user_bank_status(self, telegram_id, bank_id, status_str, status):
        async with self._transaction(isolation="serializable") as connection:
            bank = await connection.fetchrow("SELECT * FROM banks WHERE bank_id=$1;", bank_id)
            if not bank:
                return bank
            bank_sql = """
            SELECT * FROM user_banks 
            WHERE user_telegram_id=$1 AND bank_id=$2
            FOR UPDATE;"""
            bank = await connection.fetchrow(bank_sql, telegram_id, bank_id)
            if not bank:
                sql = "INSERT INTO user_banks (user_telegram_id, bank_id, fav_status, tag_status) " \
                      "VALUES ($1, $2, False, False);"
                await connection.execute(sql, telegram_id, bank_id)
            sql = f"UPDATE user_banks SET {status_str}=$1 WHERE user_telegram_id=$2 AND bank_id=$3;"
            await connection.execute(sql, status, telegram_id, bank_id)
            sql = "SELECT banks.*, user_banks.fav_status, user_banks.tag_status FROM banks " \
                  "LEFT JOIN user_banks ON banks.bank_id = user_banks.bank_id " \
                  "WHERE banks.bank_id=$1 AND user_banks.user_telegram_id=$2;"
            full_bank = await connection.fetchrow(sql, bank_id, telegram_id)

        return full_bank

    async def add_bank(self, bank_name, bank_description, bank_photo, bank_url):
        sql = "INSERT INTO banks (bank_name, bank_description, bank_photo, bank_url) " \
              "VALUES ($1, $2, $3, $4) RETURNING *;"
        return await self.execute(sql, bank_name, bank_description, bank_photo, bank_url, fetchrow=True)

    async def drop_table_users(self):
        await self.execute("DROP TABLE IF EXISTS users;", execute=True)

    async def drop_table_banks(self):
        await self.execute("DROP TABLE IF EXISTS banks;", execute=True)

    async def drop_table_bank_posts(self):
        await self.execute("DROP TABLE IF EXISTS bank_posts", execute=True)

    async def drop_table_user_banks(self):
        await self.execute("DROP TABLE IF EXISTS user_banks", execute=True)

    async def drop_table_user_bank_ratings(self):
        await self.execute("DROP TABLE IF EXISTS user_bank_ratings", execute=True)

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
