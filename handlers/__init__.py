from aiogram import Router

from .news import router as news_router
from .weather import router as weather_router
from .currency import router as currency_router
from .ai import router as ai_router
from .start import router as start_router  # start/fallback — последним!

router = Router()
router.include_routers(news_router, currency_router, weather_router, ai_router, start_router)
