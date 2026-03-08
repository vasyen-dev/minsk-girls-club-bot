import asyncio
import logging
from database.requests import check_expired_events
from database.requests import cleanup_expired_promotions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scheduled_cleanup():
    while True:
        try:
            expired = await check_expired_events()
            if expired > 0:
                logger.info(f"✅ Завершено мероприятий: {expired}")
            
            promo = await cleanup_expired_promotions()
            if promo > 0:
                logger.info(f"✅ Очищено продвижений: {promo}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
        
        await asyncio.sleep(900)

async def on_startup():
    await check_expired_events()
    await cleanup_expired_promotions()
    asyncio.create_task(scheduled_cleanup())
    logger.info("🕒 Планировщик запущен")