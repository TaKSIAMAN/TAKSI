import os
import asyncio
from aiohttp import web

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ======================
# ENV
# ======================
TOKEN = os.getenv("TOKEN")
DRIVER_CHAT_ID = int(os.getenv("DRIVER_CHAT_ID", "0"))

if not TOKEN:
    raise RuntimeError("TOKEN not found in ENV")
if DRIVER_CHAT_ID == 0:
    raise RuntimeError("DRIVER_CHAT_ID not found in ENV")

# ======================
# INIT
# ======================
bot = Bot(token=TOKEN)
dp = Dispatcher()

orders = {}
driver_order = {}

# ======================
# WEB SERVER (IMPORTANT FOR RENDER)
# ======================
async def health(request):
    return web.Response(text="OK")

async def run_web():
    app = web.Application()
    app.router.add_get("/", health)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)

    await site.start()
    print(f"🌐 Web server started on port {port}")

# ======================
# START
# ======================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🚕 Такси-бот запущен\n"
        "Напиши: Откуда - Куда\n\n"
        "✨ Все поездки анонимны для других клиентов"
    )

# ======================
# ORDER CREATE
# ======================
@dp.message()
async def handle(message: types.Message):

    user_id = message.from_user.id
    text = message.text

    if not text:
        return

    if user_id in driver_order:
        return

    if "-" in text:

        order_id = len(orders) + 1

        orders[order_id] = {
            "client_id": user_id,
            "text": text
        }

        keyboard_driver = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚕 Принять заказ", callback_data=f"accept_{order_id}")]
        ])

        keyboard_client = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить заказ", callback_data=f"cancel_{order_id}")]
        ])

        await bot.send_message(
            DRIVER_CHAT_ID,
            f"🚕 НОВЫЙ ЗАКАЗ #{order_id}\n{text}",
            reply_markup=keyboard_driver
        )

        await message.answer(
            "✅ Заказ отправлен водителям 🚕\n"
            "Ты можешь отменить его кнопкой ниже",
            reply_markup=keyboard_client
        )

# ======================
# CANCEL
# ======================
@dp.callback_query(F.data.startswith("cancel_"))
async def cancel(callback: types.CallbackQuery):

    order_id = int(callback.data.split("_")[1])
    order = orders.get(order_id)

    if not order:
        await callback.answer("Заказ уже недоступен", show_alert=True)
        return

    orders.pop(order_id, None)

    for d_id, o_id in list(driver_order.items()):
        if o_id == order_id:
            driver_order.pop(d_id, None)

    await bot.send_message(order["client_id"], "❌ Ваш заказ отменён")

    await callback.message.edit_text("❌ Заказ отменён")
    await callback.answer()

# ======================
# ACCEPT
# ======================
@dp.callback_query(F.data.startswith("accept_"))
async def accept(callback: types.CallbackQuery):

    order_id = int(callback.data.split("_")[1])
    driver_id = callback.from_user.id

    if order_id not in orders:
        await callback.answer("Заказ недоступен", show_alert=True)
        return

    driver_order[driver_id] = order_id

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5 мин", callback_data=f"time_{order_id}_5"),
            InlineKeyboardButton(text="10 мин", callback_data=f"time_{order_id}_10"),
        ],
        [
            InlineKeyboardButton(text="15 мин", callback_data=f"time_{order_id}_15"),
            InlineKeyboardButton(text="20 мин", callback_data=f"time_{order_id}_20"),
        ],
    ])

    await bot.send_message(
        driver_id,
        "⏱️ Выбери время прибытия:",
        reply_markup=keyboard
    )

    await callback.message.edit_text(f"🚕 Заказ #{order_id} принят")
    await callback.answer()

# ======================
# TIME
# ======================
@dp.callback_query(F.data.startswith("time_"))
async def set_time(callback: types.CallbackQuery):

    , order_id, minutes = callback.data.split("")
    order_id = int(order_id)

    driver_id = callback.from_user.id
    order = orders.get(order_id)

    if order:
        await bot.send_message(
            order["client_id"],
            f"🚕 Водитель приедет через {minutes} минут"
        )

    driver_order.pop(driver_id, None)
    orders.pop(order_id, None)

    await callback.message.edit_text("✅ Отправлено клиенту 🚕")
    await callback.answer()

# ======================
# MAIN
# ======================
async def main():
    print("🚕 Bot starting...")

    await run_web()          # 🔥 КЛЮЧЕВО ДЛЯ RENDER
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())