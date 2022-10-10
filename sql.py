import asyncio
import asyncpg
import logging
from config import PG_USER, PG_PASS, DB_URL


logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)
async def create_pool():
    # PG_USER ='postgres'
    # PG_PASS = 'mysecretpassword'
    # host = '192.168.216.134'
    return await asyncpg.create_pool(DB_URL)

    
if __name__ == '__main__':
    loop = asyncio.get_event_loop()