import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = 'YOUR_TOKEN'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

events = {}
participants = {}
ADMIN_ID = 'ADMIN_ID'

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Используй /help, чтобы увидеть список команд.")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = """
📜 **Команды:**
/start - Запуск бота
/help - Помощь
/events - Список мероприятий
/addevent <название> <ссылка> <дата> [время] - Добавить мероприятие
/deleteevent <ID> - Удалить мероприятие
/removeuser <ID мероприятия> <ID пользователя> - Исключить участника
/myid - Узнать свой ID
    """
    await message.answer(help_text)

@dp.message(Command("myid"))
async def cmd_myid(message: types.Message):
    await message.answer(f"Ваш ID: {message.from_user.id}")

@dp.message(Command("addevent"))
async def cmd_add_event(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    try:
        args = message.text.split(maxsplit=3)
        event_name, event_link, event_date = args[1:]
        
        try:
            if " " in event_date:
                date_str, time_str = event_date.split()
                event_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            else:
                event_datetime = datetime.strptime(event_date, "%Y-%m-%d")
        except ValueError:
            await message.answer("Неверный формат даты. Используйте: YYYY-MM-DD [HH:MM]")
            return
        
        event_id = len(events) + 1
        events[event_id] = {"name": event_name, "link": event_link, "datetime": event_datetime}
        await message.answer(f"Мероприятие '{event_name}' добавлено!")
    except ValueError:
        await message.answer("Формат: /addevent <название> <ссылка> <дата> [время]")

@dp.message(Command("deleteevent"))
async def cmd_delete_event(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    
    try:
        event_id = int(message.text.split()[1])
        if events.pop(event_id, None):
            participants.pop(event_id, None)
            await message.answer(f"Мероприятие {event_id} удалено.")
        else:
            await message.answer("Не найдено.")
    except (IndexError, ValueError):
        await message.answer("Формат: /deleteevent <ID>")

@dp.message(Command("events"))
async def cmd_show_events(message: types.Message):
    if not events:
        await message.answer("Нет мероприятий.")
        return
    
    sorted_events = sorted(events.items(), key=lambda x: x[1]["datetime"])
    builder = InlineKeyboardBuilder()
    for event_id, event in sorted_events:
        event_datetime = event["datetime"].strftime("%Y-%m-%d %H:%M")
        builder.button(text=f"{event['name']} ({event_datetime})", callback_data=f"event_{event_id}")
    builder.adjust(1)
    await message.answer("Выберите мероприятие:", reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data.startswith('event_'))
async def process_event_callback(callback_query: types.CallbackQuery):
    event_id = int(callback_query.data.split('_')[1])
    event = events.get(event_id)
    if not event:
        await callback_query.answer("Не найдено.")
        return
    
    user_id = callback_query.from_user.id
    is_participant = user_id in participants.get(event_id, set())
    
    builder = InlineKeyboardBuilder()
    if is_participant:
        builder.button(text="Отменить участие", callback_data=f"leave_{event_id}")
    else:
        builder.button(text="Записаться", callback_data=f"join_{event_id}")
    builder.button(text="Список участников", callback_data=f"list_{event_id}")
    builder.adjust(1)
    
    await callback_query.message.edit_text(
        f"{event['name']}\nСсылка: {event['link']}\nДата: {event['datetime'].strftime('%Y-%m-%d %H:%M')}",
        reply_markup=builder.as_markup()
    )
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith('join_'))
async def process_join_callback(callback_query: types.CallbackQuery):
    event_id = int(callback_query.data.split('_')[1])
    user_id = callback_query.from_user.id
    participants.setdefault(event_id, set()).add(user_id)
    await callback_query.answer("Вы записаны!")
    await process_event_callback(callback_query)

@dp.callback_query(lambda c: c.data.startswith('leave_'))
async def process_leave_callback(callback_query: types.CallbackQuery):
    event_id = int(callback_query.data.split('_')[1])
    user_id = callback_query.from_user.id
    participants.get(event_id, set()).discard(user_id)
    await callback_query.answer("Вы отменили участие.")
    await process_event_callback(callback_query)

@dp.callback_query(lambda c: c.data.startswith('list_'))
async def process_list_callback(callback_query: types.CallbackQuery):
    event_id = int(callback_query.data.split('_')[1])
    users = participants.get(event_id, set())
    
    if not users:
        await callback_query.answer("Нет участников.")
        return
    
    users_list = []
    for user_id in users:
        try:
            chat = await callback_query.bot.get_chat(user_id)
            users_list.append(f"@{chat.username}" if chat.username else f"User ID: {user_id}")
        except Exception:
            users_list.append(f"User ID: {user_id}")
    
    text = "Участники:\n" + "\n".join(users_list)
    text = text[:200] + "..." if len(text) > 200 else text
    await callback_query.answer(text)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
