import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ======================
TOKEN = "8946041096:AAH7nTs3Wj0VNFlFYjynNuo2svkCpdCaSGk"
DRIVER_CHAT_ID = -1003979477759
# ======================

bot = Bot(token=TOKEN)
dp = Dispatcher()

orders = {}         # order_id → данные заказа
driver_order = {}   # driver_id → order_id


# ======================
# START
# ======================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🚕 Такси-бот запущен\nОтправь: Откуда - Куда")


# ======================
# СОЗДАНИЕ ЗАКАЗА
# ======================
@dp.message()
async def handle(message: types.Message):

    user_id = message.from_user.id
    text = message.text

    if not text:
        return

    print("DEBUG:", user_id, text)

    # 🚕 если водитель уже в процессе заказа → это игнорим тут
    if user_id in driver_order:
        return

    # ======================
    # новый заказ
    # ======================
    if "-" in text:

        order_id = len(orders) + 1

        orders[order_id] = {
            "client_id": user_id,
            "text": text
        }

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚕 Принять заказ",
                    callback_data=f"accept_{order_id}"
                )
            ]
        ])

        await bot.send_message(
            DRIVER_CHAT_ID,
            f"🚕 НОВЫЙ ЗАКАЗ #{order_id}\n{text}",
            reply_markup=keyboard
        )

        await message.answer("✅ Заказ отправлен водителям 🚕")


# ======================
# ПРИНЯТИЕ ЗАКАЗА
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
            InlineKeyboardButton(text="7 мин", callback_data=f"time_{order_id}_7"),
        ],
        [
            InlineKeyboardButton(text="10 мин", callback_data=f"time_{order_id}_10"),
            InlineKeyboardButton(text="15 мин", callback_data=f"time_{order_id}_15"),
        ],
        [
            InlineKeyboardButton(text="20 мин", callback_data=f"time_{order_id}_20"),
            InlineKeyboardButton(text="25 мин", callback_data=f"time_{order_id}_25"),
        ],
    ])

    await bot.send_message(
        driver_id,
        "⏱ Выбери время прибытия:",
        reply_markup=keyboard
    )

    await callback.message.edit_text(f"🚕 Заказ #{order_id} принят")
    await callback.answer()


# ======================
# ВЫБОР ВРЕМЕНИ
# ======================
@dp.callback_query(F.data.startswith("time_"))
async def set_time(callback: types.CallbackQuery):

    _, order_id, minutes = callback.data.split("_")
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
# START BOT
# ======================
async def main():
    print("🚕 Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())