import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# --- НАСТРОЙКИ ---
# Токен берется из настроек Render (Environment Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8910395897

GAMES = {
    "gta6_std": {"name": "GTA VI Standard", "price": "1190 ₽"},
    "gta6_ult": {"name": "GTA VI Ultimate", "price": "1690 ₽"},
}

class OrderState(StatesGroup):
    waiting_for_contact = State()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def main_menu():
    kb = [
        [InlineKeyboardButton(text="🎮 Каталог игр", callback_data="catalog")],
        [InlineKeyboardButton(text="📞 Связаться", url="https://t.me/PlayStationgame5")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def catalog_menu():
    kb = []
    for key, game in GAMES.items():
        kb.append([InlineKeyboardButton(text=f"{game['name']} — {game['price']}", callback_data=f"buy_{key}")])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("👋 Привет! Выбери игру:", reply_markup=main_menu())

@dp.callback_query(F.data == "catalog")
async def show_catalog(call: CallbackQuery):
    await call.message.edit_text("📋 <b>Доступные игры:</b>", reply_markup=catalog_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "back")
async def back_to_menu(call: CallbackQuery):
    await call.message.edit_text("Главное меню:", reply_markup=main_menu())

@dp.callback_query(F.data.startswith("buy_"))
async def ask_contact(call: CallbackQuery, state: FSMContext):
    game_key = call.data.replace("buy_", "")
    game = GAMES[game_key]
    await state.update_data(game=game["name"], price=game["price"])
    await call.message.edit_text(f"✅ Вы выбрали: <b>{game['name']}</b>\n💰 {game['price']}\n\n✍️ Напишите ваш @username для связи:", parse_mode="HTML")
    await state.set_state(OrderState.waiting_for_contact)

@dp.message(OrderState.waiting_for_contact)
async def process_order(message: Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user
    admin_text = f"🔔 <b>НОВЫЙ ЗАКАЗ!</b>\n🎮 {data['game']}\n💰 {data['price']}\n📞 {message.text}\n👤 @{user.username}"
    
    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
        await message.answer("✅ Заявка отправлена!", reply_markup=main_menu())
    except Exception as e:
        print(e)
    await state.clear()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Запускаем веб-сервер (Render требует открытый порт)
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
