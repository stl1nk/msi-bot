from aiogram import Dispatcher, Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import pymysql
from config import BOT_TOKEN, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, ADMIN_ID
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
bot = Bot(token=BOT_TOKEN)
dp=Dispatcher( storage=MemoryStorage())
manager_queue = None
db_connection = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    cursorclass=pymysql.cursors.DictCursor
)
admin_list = ADMIN_ID
manager_list = []
ban_list = []
user_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
user_keyboard.add(KeyboardButton("Знайти технічного менеджера")).add(KeyboardButton("Знайти маркетингового менеджера"))
manager_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
manager_keyboard.add(KeyboardButton("Перейти на першого по черзі користувача"))
exit_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
exit_keyboard.add(KeyboardButton("Вийти"))

def create_users_table():
    with db_connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_name VARCHAR(255),
                user_id BIGINT ,
                manager_id BIGINT,
                manager VARCHAR(255)
            )
        """)
    db_connection.commit()
create_users_table()

def create_manager_table():
    with db_connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS managers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                manager VARCHAR(255),
                manager_id BIGINT 
            )
        """)
    db_connection.commit()
create_manager_table()

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
        with db_connection.cursor() as cursor:
                    cursor.execute('SELECT * FROM managers WHERE manager != "ban"')
                    curs = cursor.fetchall()
                    for ret in curs:
                        manager_list.append(ret["manager_id"])
                    cursor.execute('SELECT * FROM managers WHERE manager = "ban"')
                    curs = cursor.fetchall()
                    for ret in curs:
                        if ret["manager_id"] not in ban_list:
                            ban_list.append(ret["manager_id"])
        if message.from_user.id in ban_list:
            pass
        elif message.from_user.id in admin_list:
            await bot.send_message(message.from_user.id,"Команди адміна:\n/add_tex_manager\n/add_market_manager\n/delete_tex_manager\n/delete_market_manager\n/all_managers\n/unban_allusers")
        elif message.from_user.id in manager_list:
            await bot.send_message(message.from_user.id, "меню менеджера", reply_markup=manager_keyboard)
        elif message.from_user.id not in manager_list and message.from_user.id not in admin_list:
            await bot.send_message(message.from_user.id, "Якщо ви хочете з'вязатися з менеджером натисність кнопку нижче\nє питтання - /help", reply_markup=user_keyboard)


@dp.message_handler(commands=['unban_allusers'])
async def add_tex_command(message: types.Message):
    if message.from_user.id in admin_list:
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT * FROM managers WHERE manager = 'ban'")
            curs = cursor.fetchall()
            for ret in curs:
                await bot.send_message(message.from_user.id, f'{ret["manager_id"]}', reply_markup=InlineKeyboardMarkup().add(
                                                   InlineKeyboardButton(f'Розбанити {ret["manager_id"]}',callback_data=f'un_{ret["manager_id"]}')))


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await bot.send_message(message.from_user.id, "help text")

@dp.message_handler(commands=['all_managers'])
async def all_managers_command(message: types.Message):
    if message.from_user.id in admin_list:
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT * FROM managers")
            curs = cursor.fetchall()
            for ret in curs:
                await bot.send_message(message.from_user.id, f'спеціалізаця: {ret["manager"]},{ret["manager_id"]} ')

@dp.message_handler(commands=['delete_tex_manager'])
async def add_tex_command(message: types.Message):
    if message.from_user.id in admin_list:
        with db_connection.cursor() as cursor:
            cursor.execute("DELETE FROM managers WHERE manager = 'tex'")
            db_connection.commit()
            await bot.send_message(message.from_user.id, "видалений")

class FSMadmin(StatesGroup):
    state_id = State()

async def add_manager_command(message: types.Message, state: FSMContext, manager_type: str):
    async with state.proxy() as data:
        try:
            state_id = data['state_id']
            with db_connection.cursor() as cursor:
                cursor.execute("INSERT INTO managers(manager, manager_id) VALUES (%s, %s)", (manager_type, state_id,))
            db_connection.commit()
            await bot.send_message(message.from_user.id, "доданий")
        except:
            await bot.send_message(message.from_user.id, "веддіть тільки цифри")


@dp.message_handler(commands=['add_market_manager'], state='*')
async def load_market_description(message: types.Message):
    global foraddfunc
    foraddfunc = 1
    await bot.send_message(message.from_user.id, "ведіть")
    await FSMadmin.state_id.set()


@dp.message_handler(commands=['add_tex_manager'], state='*')
async def load_tex_description(message: types.Message):
    global foraddfunc
    foraddfunc = 2
    await bot.send_message(message.from_user.id, "ведіть")
    await FSMadmin.state_id.set()

@dp.message_handler(state=FSMadmin.state_id)
async def loadid(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['state_id'] = message.text
        await FSMadmin.next()
    if foraddfunc == 1:
        await add_manager_command(message, state, "market")
    elif foraddfunc == 2:
        await add_manager_command(message, state, "tex")

@dp.message_handler(commands=['delete_market_manager'])
async def all_managers_command(message: types.Message):
    with db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM managers WHERE manager = 'market'")
        db_connection.commit()
        await bot.send_message(message.from_user.id, "видалений")

@dp.message_handler(commands=['getmyid'])
async def id_command(message: types.Message):
    await bot.send_message(message.from_user.id, message.from_user.id)

@dp.message_handler(commands=['ban'])
async def ban_command(message: types.Message):
    with db_connection.cursor() as cursor:
        try:
            cursor.execute("SELECT * FROM users WHERE manager_id = %s", (message.from_user.id,))
            curs = cursor.fetchall()
            for ret in curs:
                if ret["user_id"]:
                    ban_id=ret["user_id"]
            cursor.execute("INSERT INTO managers(manager_id, manager) VALUES (%s, 'ban')",(ban_id,))
            db_connection.commit()
            cursor.execute("DELETE FROM users WHERE manager_id = %s", (message.from_user.id,))
            db_connection.commit()
            await bot.send_message(chat_id=ban_id, text='ви забанені', reply_markup=types.ReplyKeyboardRemove())

        except:
            pass
@dp.message_handler(commands=['exit_from_manager'])
async def exit_manager_command(message: types.Message):
    if message.from_user.id not in ban_list:
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (message.from_user.id,))
            curs = cursor.fetchall()
            for ret in curs:
                if ret["user_id"]:
                    await bot.send_message(chat_id=ret["manager_id"], text="Користувач вийшов з чату з вами")
            cursor.execute("DELETE FROM users WHERE user_id = %s", (message.from_user.id,))
            db_connection.commit()
            await bot.send_message(message.from_user.id, text="Ви вийшли з чату", reply_markup=user_keyboard)

@dp.message_handler(commands=['exit_from_user'])
async def exit_user_command(message: types.Message):
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE manager_id = %s", (message.from_user.id,))
        curs = cursor.fetchall()
        for ret in curs:
            if ret["user_id"]:
                await bot.send_message(chat_id=ret["user_id"], text="Менеджер вийшов з чату з вами")
        cursor.execute("DELETE FROM users WHERE manager_id = %s", (message.from_user.id,))
        db_connection.commit()
        await bot.send_message(message.from_user.id, text="Ви вийшли з чату")

@dp.message_handler()
async def echo(message: types.Message):
    try:

        with db_connection.cursor() as cursor:
                    cursor.execute('SELECT * FROM managers WHERE manager = "ban"')
                    curs = cursor.fetchall()
                    for ret in curs:
                        ban_list.append(ret["manager_id"])
        if message.from_user.id not in ban_list:

            with db_connection.cursor() as cursor:
                cursor.execute('SELECT * FROM managers WHERE manager != "ban"')
                curs = cursor.fetchall()
                for ret in curs:
                    manager_list.append(ret["manager_id"])
                if message.from_user.id not in manager_list and message.text != "/exit_from_manager" :
                        cursor.execute("SELECT * FROM users WHERE user_id = %s", (message.from_user.id,))
                        curs = cursor.fetchall()
                        for ret in curs:
                            if ret["manager_id"]:
                                if message.text == "Знайти менеджера":
                                    await bot.send_message(message.from_user.id, "Якщо ви хочете вийти з чату - /exit_from_manager")
                                else:
                                    try:
                                        await bot.send_message(chat_id=ret["manager_id"], text=message.text)
                                    except:
                                        pass
                elif message.from_user.id in manager_list and message.text != "/exit_from_user" and message.text != "Перейти на першого по черзі користувача":
                    cursor.execute("SELECT * FROM users WHERE manager_id = %s", (message.from_user.id,))
                    curs = cursor.fetchall()
                    for ret in curs:
                        if message.text == "Знайти користувача":
                            await bot.send_message(message.from_user.id, "Якщо ви хочете вийти з чату - /exit_from_user")
                        else:
                            try:
                                await bot.send_message(chat_id=ret["user_id"], text=message.text)
                            except:
                                pass

            if message.text == "Знайти маркетингового менеджера":
                with db_connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM users WHERE user_id = %s", (message.from_user.id,))
                    if cursor.fetchone():
                        cursor.execute("SELECT COUNT(*) as dif_id FROM users;")
                        ret = cursor.fetchone()
                        if ret:
                           await bot.send_message(message.from_user.id, f'Ми вже шукаємо вам менеджера, це може зайняти певний час\n Людей у черзі:{ret["dif_id"]}')
                    else:
                        cursor.execute('INSERT INTO users(user_id, user_name, manager) VALUES (%s, %s, "market")', (message.from_user.id, message.from_user.first_name))
                        db_connection.commit()
                        cursor.execute("SELECT COUNT(*) as dif_id FROM users;")
                        ret = cursor.fetchone()
                        if ret:
                            await bot.send_message(message.from_user.id, f'Шукаємо вам менеджера...\n Людей у черзі:{ret["dif_id"]}' , reply_markup=exit_keyboard)
                        with db_connection.cursor() as cursor:
                            cursor.execute('SELECT manager_id FROM managers WHERE manager = "market"')
                            curs = cursor.fetchall()
                            for ret in curs:
                                manager_id = ret["manager_id"]
                        with db_connection.cursor() as cursor:
                            cursor.execute("SELECT * FROM users WHERE user_id=%s", (message.from_user.id,))
                            curs = cursor.fetchall()
                            for ret in curs:
                                try:
                                    await bot.send_message(chat_id=manager_id,
                                           text="З вами хоче зв'язатися користувач, якщо ви хочете з'вязатися з користувачем нажміть кнопку нижче",
                                           reply_markup=InlineKeyboardMarkup().add(
                                               InlineKeyboardButton(f'Звязатися з {ret["user_name"]}(id:{ret["user_id"]})',callback_data=f'conn_{ret["user_id"]}')))
                                except:
                                   await bot.send_message(message.from_user.id, "Менеджера ще не призначено")

            elif message.text == "Знайти технічного менеджера" :
                with db_connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM users WHERE user_id = %s", (message.from_user.id,))
                    if cursor.fetchone():
                        cursor.execute("SELECT COUNT(*) as dif_id FROM users;")
                        ret = cursor.fetchone()
                        if ret:
                            await bot.send_message(message.from_user.id,f'Ми вже шукаємо вам менеджера, це може зайняти певний час\n Людей у черзі:{ret["dif_id"]}')
                    else:
                        cursor.execute('INSERT INTO users(user_id, user_name, manager) VALUES (%s, %s, "market")', (message.from_user.id, message.from_user.first_name))
                        db_connection.commit()
                        cursor.execute("SELECT COUNT(*) as dif_id FROM users;")
                        ret = cursor.fetchone()
                        if ret:
                            await bot.send_message(message.from_user.id, f'Шукаємо вам менеджера...\n Людей у черзі:{ret["dif_id"]}',reply_markup=exit_keyboard)
                        with db_connection.cursor() as cursor:
                            cursor.execute('SELECT manager_id FROM managers WHERE manager = "tex"')
                            curs = cursor.fetchall()
                            for ret in curs:
                                manager_id = ret["manager_id"]
                        with db_connection.cursor() as cursor:
                            cursor.execute("SELECT * FROM users WHERE user_id=%s", (message.from_user.id,))
                            curs = cursor.fetchall()
                            for ret in curs:
                                try:
                                    await bot.send_message(chat_id=manager_id, text="З вами хоче зв'язатися користувач, якщо ви хочете з'вязатися з користувачем нажміть кнопку нижче",reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(f'Звязатися з {ret["user_name"]}(id:{ret["user_id"]})',callback_data=f'conn_{ret["user_id"]}')))
                                except:
                                    await bot.send_message(message.from_user.id, "Менеджера ще не призначено")

            elif message.text == "Вийти":
                with db_connection.cursor() as cursor:
                    cursor.execute("DELETE FROM users WHERE user_id = %s", (message.from_user.id,))
                    db_connection.commit()
                await bot.send_message(message.from_user.id, "Ви вийшли з черги", reply_markup=user_keyboard)

            elif message.text == "Перейти на першого по черзі користувача":
                with db_connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM managers WHERE manager_id=%s", (message.from_user.id,))
                    curs = cursor.fetchall()
                    for ret in curs:
                        manager_queue = ret["manager"]
                        if manager_queue == "market":
                            cursor.execute("SELECT * FROM users WHERE manager = 'market'")
                        elif manager_queue == "tex":
                            cursor.execute("SELECT * FROM users WHERE manager = 'tex'")
                    curs = cursor.fetchall()
                    for ret in curs:
                        if ret["user_id"]:
                            await bot.send_message(chat_id=ret["user_id"], text="Менеджер вийшов з чату з вами")
                    cursor.execute("DELETE FROM users WHERE manager_id = %s", (message.from_user.id,))
                    cursor.execute( """UPDATE users SET manager_id = %s WHERE id = (SELECT min_id FROM (SELECT MIN(id) as min_id FROM users) as temp)""",(message.from_user.id,))
                    cursor.execute("SELECT * FROM users WHERE manager_id = %s", (message.from_user.id,))
                    curs = cursor.fetchall()
                    for ret in curs:
                        await bot.send_message(chat_id=ret["user_id"],text="Менеджер з'вязався з вами!\nВийти з чату - /exit_from_manager")
                        await bot.send_message(message.from_user.id, f'Ви перейшли на користувача(id: {ret["user_id"]})\nВийти з чату - /exit_from_user')
                db_connection.commit()
    except:
        await message.reply("помилка", reply_markup=ReplyKeyboardRemove)

@dp.callback_query_handler(lambda c: c.data.startswith('un_'))
async def process_callback_button(callback_query: types.CallbackQuery):
    global ban_list
    user_id = callback_query.data.split('_')[1]
    with db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM managers WHERE manager_id = %s", (user_id,))
    db_connection.commit()
    ban_list.remove(user_id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="разбанений")

@dp.callback_query_handler(lambda c: c.data.startswith('conn_'))
async def process_callback_button(callback_query: types.CallbackQuery):
    user_id = callback_query.data.split('_')[1]
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🇺🇦", callback_data=f'no data')))
    with db_connection.cursor() as cursor:
        cursor.execute("UPDATE users SET manager_id = %s WHERE user_id = %s",
            (callback_query.from_user.id, user_id))
    db_connection.commit()
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
    curs = cursor.fetchall()
    for ret in curs:
        try:
            if ret["user_id"]:
                await bot.send_message(callback_query.from_user.id, f'Ви успішно звязались з \nкористувачем(id:{user_id})!\nВийти з чату - /exit_from_user')
                await bot.send_message(chat_id=user_id, text="Менеджер з'вязався з вами!\nВийти з чату - /exit_from_manager")
        except:
            await bot.send_message(callback_query.message.chat.id, "Користувач вийшов з черги")

if __name__ == "__main__":
    asyncio.run(main())