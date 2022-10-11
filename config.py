from aiogram.dispatcher import Dispatcher
from aiogram import Bot
import os
from dotenv_config import load_dotenv
load_dotenv()

API_TOKEN = os.getenv('BOT_TOKEN')
ADMINS = os.getenv('ADMINS')
#bot = Bot(token=API_TOKEN, parse_mode='HTML')
#dp = Dispatcher(bot)
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

# webhook settings
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# webserver settings
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT', default=8000)
DB_URL = os.getenv('HEROKU_POSTGRESQL_SILVER_URL')
