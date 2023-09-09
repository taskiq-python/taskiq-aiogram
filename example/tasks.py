import asyncio

from aiogram import Bot
from taskiq import TaskiqDepends

from example.tkq import broker


@broker.task(task_name="my_task")
async def my_task(chat_id: int, bot: Bot = TaskiqDepends()) -> None:
    print("I'm a task")
    await asyncio.sleep(4)
    await bot.send_message(chat_id, "task completed")
