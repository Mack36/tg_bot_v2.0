import asyncio
import asyncpg
from aiogram import types, Bot, Dispatcher
from asyncpg import Connection, Record, Pool
from asyncpg.exceptions import UniqueViolationError
#from sql import create_pool
from datetime import datetime
#from config import DB_URL, dp, db
import config
import logging

#loop = asyncio.get_event_loop()
#
logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)

class DBCommands():
    #loop = asyncio.get_event_loop()
    async def create_conn(self):
        #oop = asyncio.get_event_loop(dp)
        #self.pool = loop.run_until_complete(asyncpg.create_pool(config.DB_URL))
        self.pool = await asyncpg.create_pool(config.DB_URL)

    ADD_NEW_USER = "INSERT INTO users(id, username, surname, nickname, state, phonenum, itemviewed, catviewed) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id"
    GET_USER_BY_ID = "SELECT * FROM users WHERE id = $1"
    GET_CATEGORIES = "SELECT * from categories ORDER BY cat_id"
    GET_ITEMS = "SELECT * from items ORDER BY id"
    UPDATE_USER_STATE = "UPDATE users SET state = $1 WHERE id = $2"
    UPDATE_USER_PHONENUM = "UPDATE users SET phonenum = $1 WHERE id = $2"
    GET_MENU_IMAGE = "SELECT image FROM menu where menu = $1"
    LOAD_USER_CART = "SELECT * FROM carts where userid = $1"
    ADD_INTO_USER_CART = "INSERT INTO carts (userid, itemid) VALUES ($1, $2)"
    DELETE_FROM_CART = "DELETE FROM carts WHERE userid = $1 and itemid = $2"
    SEARCH_IN_CART = "SELECT * FROM carts WHERE userid = $1 and itemid = $2"
    CLEAR_CART = "DELETE FROM carts where userid = $1"
    UPD_TMP_ITEM = "UPDATE users SET itemviewed = $1 WHERE id = $2"
    LOAD_TMP_ITEM = "SELECT itemviewed FROM users where id = $1"
    UPD_TMP_CAT = "UPDATE users SET catviewed = $1 WHERE id = $2"
    LOAD_TMP_CAT = "SELECT catviewed FROM users where id = $1"
    CREATE_ORDER = "INSERT INTO orders(items, user_id, comment, date, state) VALUES ($1, $2, $3, $4, $5) RETURNING id"
    CANCEL_ORDER = "UPDATE orders SET state = 0 WHERE id = $1"
    FIND_ACT_ORDERS_BY_USERID = "SELECT * FROM orders WHERE user_id = $1 and state = $2"
    FIND_ORDER_BY_ORDERID = "SELECT * FROM orders WHERE id = $1"
    FIND_ALL_ORDERS_BY_USERID = "SELECT * FROM orders WHERE user_id = $1 ORDER BY date"
    LOAD_ALL_ACT_ORDERS = "SELECT o.id, o.user_id, u.nickname, o.items, o.date, o.state, o.comment " \
                          "FROM orders o, users u WHERE o.user_id = u.id AND o.state = 1 ORDER BY date;"
    LOAD_ALL_DONE_ORDERS = "SELECT o.id, o.user_id, u.nickname, o.items, o.date, o.state, o.comment " \
                          "FROM orders o, users u WHERE o.user_id = u.id AND o.state = 0 ORDER BY date;"
    LOAD_ALL_ORDERS = "SELECT o.id, o.user_id, u.nickname, o.items, o.date, o.state, o.comment " \
                           "FROM orders o, users u WHERE o.user_id = u.id ORDER BY date;"


    async def add_new_user(self):
        user = types.User.get_current()
        chat_id = user.id
        username = user.first_name
        surname = user.last_name
        nickname = user.username
        state = 0
        phonenum = ""
        itemviewed = 0
        catviewed = 0
        args = chat_id, username, surname, nickname, state, phonenum, itemviewed, catviewed
        command = self.ADD_NEW_USER
        try:
            record_id = await self.pool.fetch(command, *args)
            return record_id
        except UniqueViolationError:
            pass


    async def get_user_by_id(self, user_id=0):
        command = self.GET_USER_BY_ID
        if user_id == 0:
            user_id = types.User.get_current().id
        r = await self.pool.fetch(command, user_id)
        return [dict(row) for row in r]

    async def get_categories(self):
        async with self.pool.acquire() as con:
            command = self.GET_CATEGORIES
            x = await con.fetch(command)
            # x = await con.fetch(command)
            # return [dict(row) for row in x]
            return x

    async def get_items(self):
        async with self.pool.acquire() as con:
            command = self.GET_ITEMS
            l = await con.fetch(command)
            return [dict(row) for row in l]

    async def upd_user_state(self, state):
        user = types.User.get_current()
        args = state, user.id

        command = self.UPDATE_USER_STATE
        try:
            record_id = await self.pool.fetch(command, *args)
            return record_id
        except UniqueViolationError:
            pass

    async def upd_user_phonenum(self, phonenum):
        user = types.User.get_current()
        args = phonenum, user.id

        command = self.UPDATE_USER_PHONENUM
        try:
            record_id = await self.pool.fetch(command, *args)
            return record_id
        except UniqueViolationError:
            pass

    async def get_user_state(self):
        rows = await self.get_user_by_id()
        d = [dict(row) for row in rows]
        return d[0]['state']

    async def get_menu_image(self, menu_id):
        command = self.GET_MENU_IMAGE
        return await self.pool.fetchval(command, menu_id)

    async def load_user_cart(self):
        user = types.User.get_current()
        chat_id = user.id
        command = self.LOAD_USER_CART
        r = await self.pool.fetch(command, chat_id)
        return [dict(row) for row in r]

    async def search_in_cart(self, itemid):
        user = types.User.get_current()
        chat_id = user.id
        command = self.SEARCH_IN_CART
        args = chat_id, itemid
        return await self.pool.fetchval(command, *args)

    async def add_into_cart(self, itemid):
        user = types.User.get_current()
        chat_id = user.id
        if await self.search_in_cart(itemid):
            print(f"Item {itemid} is already in your cart")
            return False
        command = self.ADD_INTO_USER_CART
        args = chat_id, itemid
        try:
            record_id = await self.pool.fetch(command, *args)
            return record_id
        except UniqueViolationError:
            pass

    async def del_from_cart(self, itemid):
        user = types.User.get_current()
        chat_id = user.id
        command = self.DELETE_FROM_CART
        args = chat_id, itemid
        return await self.pool.fetchval(command, *args)

    async def clear_cart(self):
        user = types.User.get_current()
        chat_id = user.id
        command = self.CLEAR_CART
        return await self.pool.fetchval(command, chat_id)

    async def load_tmp_item(self):
        user = types.User.get_current()
        chat_id = user.id
        command = self.LOAD_TMP_ITEM
        return await self.pool.fetchval(command, chat_id)

    async def search_in_tmp_cart(self, itemid):
        if await self.load_tmp_item() == itemid:
            return True
        return False

    async def upd_tmp_item(self, itemid):
        user = types.User.get_current()
        chat_id = user.id
        if await self.search_in_tmp_cart(itemid):
            print(f"Item {itemid} is already in your tmp cart")
            return False
        command = self.UPD_TMP_ITEM
        args = itemid, chat_id
        try:
            record_id = await self.pool.fetch(command, *args)
            return record_id
        except UniqueViolationError:
            pass

    async def load_tmp_cat(self):
        user = types.User.get_current()
        chat_id = user.id
        command = self.LOAD_TMP_CAT
        return await self.pool.fetchval(command, chat_id)

    async def upd_tmp_cat(self, catid):
        user = types.User.get_current()
        chat_id = user.id
        command = self.UPD_TMP_CAT
        args = catid, chat_id
        try:
            record_id = await self.pool.fetch(command, *args)
            return record_id
        except UniqueViolationError:
            pass

    async def create_order(self, items, comment):
        user = types.User.get_current()
        chat_id = user.id
        state = 1
        date = datetime.today()
        args = items, chat_id, comment, date, state
        command = self.CREATE_ORDER

        try:
            order_id = await self.pool.fetchval(command, *args)
            return order_id
        except UniqueViolationError:
            pass

    async def load_user_orders(self, orderid=0, state=1):
        user = types.User.get_current()
        chat_id = user.id
        if orderid == 0:
            if state != 1:
                command = self.FIND_ALL_ORDERS_BY_USERID
                r = await self.pool.fetch(command, chat_id)
            else:
                command = self.FIND_ACT_ORDERS_BY_USERID
                args = chat_id, state
                r = await self.pool.fetch(command, *args)
        else:
            command = self.FIND_ORDER_BY_ORDERID
            r = await self.pool.fetch(command, orderid)
        return [dict(row) for row in r]

    async def cancel_order_by_id(self, orderid):
        command =self.CANCEL_ORDER
        return await self.pool.fetchval(command, orderid)
    
    async def load_all_orders(self, type=1):
        if type == 3:   
            command = self.LOAD_ALL_DONE_ORDERS
        elif type == 2:
            command = self.LOAD_ALL_ACT_ORDERS
        elif type == 1:
            command = self.LOAD_ALL_ORDERS
        r = await self.pool.fetch(command)
        return [dict(row) for row in r]
