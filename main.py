import logging
from aiogram import Bot, Dispatcher, executor, types, filters
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData
import asyncio
from asyncpg import Connection, Record
from asyncpg.exceptions import UniqueViolationError
#from sql import create_pool
import re
import dbcoms
from config import WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT, API_TOKEN, WEBHOOK_URL,ADMINS


# Токен, выданный BotFather в телеграмме
#API_TOKEN = '5691852231:AAFgIfQ780Xqh1thLvarVUrlTeAGQBNxtww'
#loop = asyncio.get_event_loop()
#dbinit = loop.run_until_complete(create_pool())
# Configure logging
#logging.basicConfig(level=logging.INFO)
admins = []
admins = ADMINS.split(',')
# admins = (11626420)
#admins = (116264208, 56450364)

class Korzina:
    user = types.User.get_current()
    cart = {}
    tmpcart = 0
    tmpcartcat = 0
    async def init(self):
        self.cart = await db.load_user_cart()
        self.tmpcart = await db.load_tmp_item()
        self.tmpcartcat = await db.load_tmp_cat()

    async def add_item_tmp(self, item_id):
        await self.init()
        self.tmpcart = item_id
        await db.upd_tmp_item(item_id)

    async def add_cat_tmp(self, cat_id):
        await self.init()
        self.tmpcartcat = cat_id
        await db.upd_tmp_cat(cat_id)

    async def add_item(self, item_id):
        await self.init()
        self.cart.append(item_id)
        await db.add_into_cart(item_id)
        await db.upd_tmp_item(0)
        #print(self.cart)

    async def item_already_in_cart(self, item_id):
        await self.init()
        for item in self.cart:
            if item['itemid'] == item_id:
                return True

    async def is_cart_empty(self):
        if len(self.cart) == 0:
            return True
        return False

    async def reset_cart(self):
        self.cart.clear()
        await db.clear_cart()

    async def del_item_in_cart(self, item_id, item_index):
        self.cart.pop(item_index)
        await db.del_from_cart(item_id)

    async def create_order(self, comment):
        await self.init()
        itemlist = []
        for item in self.cart:
            itemlist.append(item['itemid'])
        #print(itemlist)
        converted_itemlist = [str(element) for element in itemlist]
        joined_string = ",".join(converted_itemlist)
        order_id = await db.create_order(joined_string, comment)
        return order_id


# Initialize bot and dispatcher

bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)
db = dbcoms.DBCommands()

def make_itemlist(items_string):
    global res
    items = items_string.split(',')
    itemlist = ""
    k = 1
    for item in items:
        for r in res:
            if int(item) == r['id']:
                itemlist += f"  {k}. {r['name']}\n"
                k += 1
    return itemlist


async def on_startup(dp):
    global cats, res
    await db.create_conn()
    cats = await db.get_categories()
    res = await db.get_items()
    #await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    for admin in admins:
        await bot.send_message(admin, 'Bot has started')

async def on_shutdown():
    await db.pool.close()
    #await bot.delete_webhook()



@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    #btn = types.KeyboardButton("Отправить номер", request_contact=True)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("О продукции 📦", "Акции 🎁", "Полезное ☝")
    keyboard.add("Об Atomy 💫", "Каталог 📕", "Отзывы 📢")
    us_id = message.from_user.id
    us_name = message.from_user.first_name
    us_sname = message.from_user.last_name
    username = message.from_user.username
    searchuser = await db.get_user_by_id()
    if not searchuser:
        await db.add_new_user()
        menutxt = f"{us_name} {us_sname}, добро пожаловать ! Текст приветствия."
    else:
        btn1 = ['Корзина 🛒', 'Оформить заказ ✅']
        keyboard.add(*btn1)
        menutxt = "Главное меню"
    if str(us_id) in admins:
        keyboard.add("Работа с заказами 📑")
    keyboard.add("Помощь❓")
    #keyboard.add(btn)
    await db.upd_user_state(1)
    await message.answer(menutxt, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Каталог 📕")
async def cmd_catalogue(message: types.Message):
    #await message.reply("Выберите категорию:")
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    i = 0
    global res, cats
    if not cats:
        cats = await db.get_categories()
    while i < len(cats):
        if len(cats) - i < 2:
            btntmp = cats[i]['cat_name']
            keyboard.add(btntmp)
        else:
            btntmp = [cats[i]['cat_name'], cats[i+1]['cat_name']]
            keyboard.add(*btntmp)
        i += 2

    btn = ['⬅ Назад', 'В главное меню ⬆']
    btn1 = ['Корзина 🛒', 'Оформить заказ ✅']
    keyboard.add(*btn1)
    keyboard.add(*btn)
    await message.answer("Выберите категорию:", reply_markup=keyboard)
    await db.upd_user_state(2)


@dp.message_handler(lambda message: message.text == "О продукции 📦")
async def about_prod(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    await message.answer('Текст о продукции...', reply_markup=keyboard)
    imgid = await db.get_menu_image('1')
    if imgid:
        await bot.send_photo(message.chat.id, photo=imgid)


@dp.message_handler(lambda message: message.text == "Добавить в корзину ✔")
async def cmd_item_chosen(message: types.Message):
    global res
    state = await db.get_user_state()
    cart = Korzina()
    await cart.init()
    if state == 4:
        for r in res:
            if r['id'] == cart.tmpcart:
                name = r['name']
        if not await cart.item_already_in_cart(cart.tmpcart):
            txt = f'{name} был добавлен в корзину'
            await cart.add_item(item_id=cart.tmpcart)
        else:
            txt = f'{name} уже есть в вашей корзине'
        await message.answer(txt)
        await db.upd_user_state(4)
        await cmd_back(message)

@dp.message_handler(lambda message: message.text == "⬅ Назад")
async def cmd_back(message: types.Message):
    state = await db.get_user_state()
    global res, cats
    cart = Korzina()
    await cart.init()
    if state == 5:
        await db.upd_user_state(2)
        await cmd_cat_chosen(message, cart.tmpcartcat)
    elif state == 3 or state == 4:
        await db.upd_user_state(1)
        await cmd_catalogue(message)
    elif state == 2:
        await db.upd_user_state(1)
        await cmd_start(message)
    else:
        await db.upd_user_state(1)
        await cmd_start(message)


@dp.message_handler(lambda message: message.text == "В главное меню ⬆")
async def cmd_main(message: types.Message):
    await db.upd_user_state(1)
    await cmd_start(message)


@dp.message_handler(lambda message: message.text == "Работа с заказами 📑")
async def order_works(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btnrow1 = ['Открытые заказы', 'Обработанные заказы']
    btnrow2 = ['Все заказы', 'Поиск']
    keyboard.add(*btnrow1)
    keyboard.add(*btnrow2)
    keyboard.add('В главное меню ⬆')
    await db.upd_user_state(10)
    await message.answer('Выберите пункт', reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Все заказы")
async def load_orders(message: types.Message, type=1):
    # types: 1 - all, 2 - all active, 3 - all done, 4 - all user by userid
    if type == 4:
        orders = await db.load_user_orders(state=0) #all user ords by userid
        userinfo = await db.get_user_by_id()
        usernickname = userinfo[0]['nickname']
    elif type == 3:
        orders = await db.load_all_orders(type=3) #LOAD_ALL_DONE_ORDERS
    elif type == 2:
        orders = await db.load_all_orders(type=2) #LOAD_ALL_ACT_ORDERS
    elif type == 1:
        orders = await db.load_all_orders(type=1) #LOAD_ALL_ORDERS
    orders_txt = ""
    orders_list = []
    for i, ord in enumerate(orders, start=1):
        state = '▶' if ord['state'] == 1 else '✅'
        orddate = ord['date'].strftime("%Y-%m-%d %H:%M")
        tmplist = make_itemlist(ord['items'])
        if len(ord['comment']) == 0:
            ordcomment = ""
        else:
            ordcomment = f"<b>note:</b> <i>{ord['comment']}</i>, "
        if type != 4:
            usernickname = ord['nickname']
            orders_txt += f"<b>{i}.</b> {state} №{ord['id']}: @{usernickname} [{orddate}] {ordcomment}выбрано:\n{tmplist}"
            orders_list.append(f"<b>{i}.</b> {state} №{ord['id']}: @{usernickname} [{orddate}] {ordcomment}выбрано:\n{tmplist}")
        else:
            orders_txt += f"<b>{i}.</b> {state} №{ord['id']}: [{orddate}] {ordcomment}выбрано:\n{tmplist}"
            orders_list.append = (f"<b>{i}.</b> {state} №{ord['id']}: [{orddate}] {ordcomment}выбрано:\n{tmplist}")
    if type == 4:
        header = f"<b>Все заказы клиента @{usernickname}:</b>"
    elif type == 3:
        header = f"<b>Все обаботанные заказы:</b>"
    elif type == 2:
        header = f"<b>Все открытые заказы:</b>"
    else:
        header = f"<b>Все заказы:</b>"
    global ordersgl, orders_listgl, headergl
    ordersgl, orders_listgl, headergl = orders, orders_list, header
    txt, kb = await prepare_inline(orders, orders_list, header)
    await message.answer(txt, reply_markup=kb)

@dp.message_handler(lambda message: message.text == "Открытые заказы")
async def load_act_orders(message: types.Message):
    await load_orders(message, type=2)

@dp.message_handler(lambda message: message.text == "Обработанные заказы")
async def load_done_orders(message: types.Message):
    await load_orders(message, type=3)

@dp.message_handler(lambda message: message.text == "Все заказы")
async def load_done_orders(message: types.Message):
    await load_orders(message, type=4)

@dp.message_handler(lambda message: message.text == "Корзина 🛒")
async def cmd_cart(message: types.Message, trigger=False):
    global cats, res
    cart = Korzina()
    await cart.init()
    itemlist = ''
    if await cart.is_cart_empty():
        await message.answer('Ваша корзина пуста')
        return False
    if not trigger:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    k = 1
    for item in cart.cart:
        for it in res:
            if item['itemid'] == it['id']:
                itemlist += f"{k}. {it['name']}\n"
                k += 1
                if not trigger:
                    keyboard.add('❌ ' + it['name'])
    if trigger:
        return itemlist
    if not trigger:
        keyboard.add('Оформить заказ ✅')
        btn = ['⬅ Назад', '🔄 Очистить']
        keyboard.add(*btn)
        helptxt = '<b>«❌ Наименование»</b> - удалить одну позицию\n<b>«🔄 Очистить»</b> - полная очистка корзины'
        await message.answer(helptxt)
        await message.answer(f'<b>🛒 Товары в вашей корзине:</b>\n{itemlist}', reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "🔄 Очистить")
async def cmd_cart_clear(message: types.Message):
    cart = Korzina()
    await cart.init()
    if await cart.is_cart_empty():
        await message.answer("Ваша корзина уже пуста")
        await cmd_start(message)
    else:
        await message.answer("Корзина очищена")
        await cart.reset_cart()
        await cmd_start(message)


@dp.message_handler(regexp=r"^❌ ")
async def cmd_cart_del_item(message: types.Message):
    global res
    cart = Korzina()
    await cart.init()
    itemname = message.text.split("❌ ", 1)[1]
    for it in res:
        if it['name'] == itemname:
            itemid = (it['id'])
    for index, item in enumerate(cart.cart, start=0):
        if item['itemid'] == itemid:
            item_index = index
    await cart.del_item_in_cart(itemid, item_index)
    if await cart.is_cart_empty():
        await message.answer("Ваша корзина пуста")
        await cmd_start(message)
    else:
        await cmd_cart(message)


async def cmd_create_order(message: types.Message, comment):
    cart = Korzina()
    orderid = await cart.create_order(comment)
    await cart.reset_cart()
    await message.answer(f"✅ Спасибо, ваш заказ принят!\nМы свяжемся с вами в ближайшее время.\nНомер вашего заказа: {orderid}")
    await cmd_main(message)
    await on_order_create(orderid)


@dp.message_handler(lambda message: message.text == "Оформить заказ ✅")
async def order_get_comment(message: types.Message):
    itemlist = await cmd_cart(message, True)
    if itemlist:
        await db.upd_user_state(5)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn = ['⬅ Назад', 'В главное меню ⬆']
        keyboard.add(types.KeyboardButton("Отправить номер", request_contact=True))
        keyboard.add(*btn)
        await message.answer(f"<b>🛒 Товары в вашей корзине:</b>\n{itemlist}")
        await message.answer("Оставьте пожалуйста свой контактный номер. чтобы продолжить\n"
                             "Можете ввести номер вручную, либо нажать на кноку \"Отправить номер\"", reply_markup=keyboard)
    else:
        #await message.answer("Ваша корзина пуста!")
        await db.upd_user_state(1)
        await cmd_start(message)


@dp.message_handler(content_types='contact')
async def proc_contact(message: types.Message):
    state = await db.get_user_state()
    if state == 5:
        if message.content_type == 'contact':
            await db.upd_user_phonenum(message.contact.phone_number)
        else:
            if not re.search('^\+?998[0-9]{9}$', message.text):
                await message.answer('Некорректный номер, введите номер в формате 998XY1234567')
                return False
            else:
                if re.search('^[^\+]*', message.text):
                    message.text = "+" + message.text
                await db.upd_user_phonenum(message.text)
        await message.answer('Cохранено')
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Пропустить")
        btn = ['⬅ Назад', 'В главное меню ⬆']
        keyboard.add(*btn)
        await message.answer("Добавьте комментарий к заказу:", reply_markup=keyboard)
        await db.upd_user_state(6)


async def on_order_create(orderid):
    order = await db.load_user_orders(orderid)
    global res
    itemlist = order[0]['items'].split(',')
    orderdate = order[0]['date']
    ordercomment = order[0]['comment']
    listtext = ''
    print(itemlist)
    k = 1
    for i in itemlist:
        for r in res:
            if r['id'] == int(i):
                listtext += f"{k}. {r['name']}\n"
                k += 1
    userid = order[0]['user_id']
    userdata = await db.get_user_by_id(userid)
    username = userdata[0]['username']
    usersurname = userdata[0]['surname']
    usernickname = userdata[0]['nickname']
    userphonenum = userdata[0]['phonenum']
    listtext += f'☎ {userphonenum}\n'
    if len(ordercomment) > 0:
        listtext += f'<b>Комментарий:</b> <i>{ordercomment}</i>\n'
    choice = InlineKeyboardMarkup(row_width=1)
    btna = InlineKeyboardButton(text="Работа с заказами", callback_data="order_works")
    choice.insert(btna)
    for admin in admins:
        await bot.send_message(admin, f"<b>✳ {orderdate} Заказ № {orderid}\n<b>От</b> "
                                  f"[@{usernickname}] {username} {usersurname}:</b>\n{listtext}", reply_markup=choice)

async def prepare_inline(orderslist, orderslistln, header, page=1):
    kb = InlineKeyboardMarkup(row_width=5)
    max_recs_per_page = 10
    divisionleft = len(orderslistln) % max_recs_per_page
    pagestotal = len(orderslistln) // max_recs_per_page
    if divisionleft != 0:
        pagestotal += 1
    if page > pagestotal:
        page = 1
    if page < 1:
        page = pagestotal
    max_linenum_here = max_recs_per_page * page
    min_linenum_here = max_recs_per_page * (page - 1) + 1

    if len(orderslistln) >= max_recs_per_page:
        if page != pagestotal:
            lines_on_page = max_recs_per_page
            actual_maxlinenum_here = max_recs_per_page
        else:
            lines_on_page = max_recs_per_page - ((page * max_recs_per_page) - len(orderslistln))
            actual_maxlinenum_here = len(orderslistln)
    else:
        lines_on_page = len(orderslistln)
        actual_maxlinenum_here = lines_on_page
    linetoshow = ""
    newlist = []
    emptylist = []
    for linenum in range(min_linenum_here, min_linenum_here + lines_on_page):
        newlist.append(orderslist[linenum-1])
        linetoshow += orderslistln[linenum-1]
        linenum += 1
    empty_btnsnum = max_recs_per_page - lines_on_page
    if empty_btnsnum > 0:
        if empty_btnsnum > 4:
            empty_btnsnum = 4
        for n in range(1, empty_btnsnum + 1):
            emptylist.append(' ')

    if emptylist:
        kb.add(*[InlineKeyboardButton(str(itr + 1), callback_data='o' + str(listelement['id'])) for itr, listelement in
                 enumerate(newlist)], *[InlineKeyboardButton(emptyelement, callback_data='nothing') for emptyelement in emptylist])
    else:
        kb.add(*[InlineKeyboardButton(str(itr + 1), callback_data='o' + str(listelement['id'])) for itr, listelement in
                   enumerate(newlist)])
    header += f'\n<b>Результаты {min_linenum_here}-{actual_maxlinenum_here} из {len(orderslistln)}:</b>'
    # return kb
    backcbdata = "back"+str(page)
    fwdcbdata = "fwd"+str(page)
    allbtndata = 'all' + str(page)
    allbtndata = "nothing"
    if pagestotal == 1:
        backcbdata = fwdcbdata = "nothing"
    kb.add(InlineKeyboardButton("⬅", callback_data=backcbdata),
                 InlineKeyboardButton(str(page), callback_data=allbtndata),
                 InlineKeyboardButton("➡", callback_data=fwdcbdata))
    final_text = (f'{header}\n{linetoshow}')

    return final_text, kb

async def prepare_add_inline(open: True):
    kb = InlineKeyboardMarkup(row_width=3)
    if open:
        midbtn = InlineKeyboardButton("✅", callback_data='close_order')
    else:
        midbtn = InlineKeyboardButton("🔄", callback_data='open_order')

    kb.add(InlineKeyboardButton("⏪", callback_data='prev_order'),
           midbtn, InlineKeyboardButton("⏩", callback_data='next_order'))

    kb.add(InlineKeyboardButton("Назад к списку", callback_data='to_list'),
           InlineKeyboardButton("В главное меню", callback_data='exit'))
    return kb

@dp.message_handler()
async def cmd_cat_chosen(message: types.Message, catchosen=0):
    global cats, res
    state = await db.get_user_state()
    itemlist = []
    cart = Korzina()
    await cart.init()
    if state == 2:
        for cat in cats:
            if message.text == cat['cat_name'] or (not catchosen == 0 and cat['cat_id'] == cart.tmpcartcat):
                #await message.reply(f'Выбрана категория: {message.text}')
                for n in res:
                    if n['cat_id'] == cat['cat_id']:
                        itemlist.append(n)
                #print(res)
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                k = 0
                while k < len(itemlist):
                    if len(itemlist) - k < 2:
                        btntmp = itemlist[k]['name']
                    else:
                        btntmp = [itemlist[k]['name'], itemlist[k + 1]['name']]
                    k += 2
                    if len(itemlist) > 1:
                        keyboard.add(*btntmp)
                    else:
                        keyboard.add(btntmp)
                    #keyboard.add(elem[1])
                if catchosen > 0:
                    catname = cat['cat_name']
                else:
                    catname = message.text
                btn1 = ['Корзина 🛒', 'Оформить заказ ✅']
                keyboard.add(*btn1)
                btn = ['⬅ Назад', 'В главное меню ⬆']
                keyboard.add(*btn)
                await message.answer(f'Выбрана категория: {catname}', reply_markup=keyboard)
                #print(cat)
                await bot.send_photo(chat_id=message.chat.id, photo=cat['photo'])
                await db.upd_user_state(3)
                await cart.add_cat_tmp(cat['cat_id'])
                catchosen = 0
                state = 3
    if state == 3:
        for item in res:
            if message.text == item['name']:
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                await message.reply(f'{message.text}')
                await bot.send_photo(chat_id=message.chat.id, photo=item['photo'])
                if len(item['item_txt']) > 0:
                    await bot.send_message(message.chat.id, item['item_txt'])
                keyboard.add('Добавить в корзину ✔')
                btn1 = ['Корзина 🛒', 'Оформить заказ ✅']
                keyboard.add(*btn1)
                btn = ['⬅ Назад', 'В главное меню ⬆']
                keyboard.add(*btn)
                price = item['price']
                await message.answer(f'💵 Цена: {price} сум', reply_markup=keyboard)
                await db.upd_user_state(4)
                await cart.add_item_tmp(item['id'])

    if state == 5:
        await proc_contact(message)
        #await cart.create_order(comment)
    if state == 6:
        if message.text == "Пропустить":
            comment = ""
        else:
            comment = message.text
        await cmd_create_order(message, comment)


@dp.callback_query_handler(text_contains="order_works")
async def go_to_order_works(call: CallbackQuery, all=False):
    await call.answer(cache_time=60)
    await order_works(call.message)


@dp.callback_query_handler(filters.Regexp(r'^o[0-9]'))
async def inline_ord_selected(call: CallbackQuery):
    print(call.data)
    orderid = int(call.data.split('o')[1])
    global ordersgl, orders_listgl
    for i in range(0, len(ordersgl)):
        if ordersgl[i]['id'] == orderid:
            order_txt = orders_listgl[i]
            order_open = True if ordersgl[i]['state'] == 1 else False
            userid = ordersgl[i]['user_id']
            user = await db.get_user_by_id(userid)
            userphonenum = user[0]['phonenum']
            break

    order_txt += f'☎ {userphonenum}'
    kb = await prepare_add_inline(order_open)
    await bot.answer_callback_query(callback_query_id=call.id)
    await bot.edit_message_text(order_txt, call.from_user.id, call.message.message_id, parse_mode="HTML", reply_markup=kb)


@dp.callback_query_handler(filters.Regexp(r'back'))
async def inline_back_selected(call: CallbackQuery):
    print(call.data)
    pgnum = int(call.data[4]) - 1
    global ordersgl, orders_listgl, headergl
    await bot.answer_callback_query(callback_query_id=call.id)
    txt, kb = await prepare_inline(ordersgl, orders_listgl, headergl, pgnum)
    await bot.edit_message_text(txt, call.from_user.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")


@dp.callback_query_handler(filters.Regexp(r'fwd'))
async def inline_fwd_selected(call: CallbackQuery):
    print(call.data)
    pgnum = int(call.data[3]) + 1
    global ordersgl, orders_listgl, headergl
    await bot.answer_callback_query(callback_query_id=call.id)
    txt, kb = await prepare_inline(ordersgl, orders_listgl, headergl, pgnum)
    await bot.edit_message_text(txt, call.from_user.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")

@dp.callback_query_handler(filters.Regexp(r'nothing'))
async def inline_fwd_selected(call: CallbackQuery):
    await bot.answer_callback_query(callback_query_id=call.id)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    '''executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )'''
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
