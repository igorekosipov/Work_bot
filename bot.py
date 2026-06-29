import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from config import BOT_TOKEN, ADMIN_IDS, PROXY_URL
from database import init_db, add_user, set_admin
from handlers.start import router as start_router
from handlers.subscription import router as sub_router
from handlers.calculator import router as calc_router
from handlers.statistics import router as stat_router
from handlers.work_calendar import router as cal_router
from handlers.support import router as support_router
from handlers.chat import router as chat_router
from handlers.admin import router as admin_router
from scheduler import start_scheduler

async def setup_admins():
    """Добавляет админов в БД при запуске"""
    for admin_id in ADMIN_IDS:
        await add_user(admin_id, "admin", "Администратор")
        await set_admin(admin_id, 1)
        print(f"Админ {admin_id} добавлен")

async def main():
    await init_db()
    await setup_admins()
    
    if PROXY_URL:
        session = AiohttpSession(proxy=PROXY_URL)
        print(f"Используется прокси: {PROXY_URL}")
    else:
        session = AiohttpSession()
        print("Прокси не используется")
    
    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    dp.include_router(start_router)
    dp.include_router(sub_router)
    dp.include_router(calc_router)
    dp.include_router(stat_router)
    dp.include_router(cal_router)
    dp.include_router(support_router)
    dp.include_router(chat_router)
    dp.include_router(admin_router)
    
    await start_scheduler(bot)
    
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
