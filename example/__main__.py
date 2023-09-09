import asyncio
import logging
import sys
from typing import Any

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from example.tasks import my_task
from example.tkq import broker

dp = Dispatcher()
bot = Bot(token="TOKEN")


@dp.startup()
async def setup_taskiq(bot: Bot, *_args: Any, **_kwargs: Any) -> None:
    # Here we check if it's a clien-side,
    # Becuase otherwise you're going to
    # create infinite loop of startup events.
    if not broker.is_worker_process:
        logging.info("Setting up taskiq")
        await broker.startup()


@dp.shutdown()
async def shutdown_taskiq(bot: Bot, *_args: Any, **_kwargs: Any) -> None:
    if not broker.is_worker_process:
        logging.info("Shutting down taskiq")
        await broker.shutdown()


@dp.message(Command("task"))
async def message(message: types.Message) -> None:
    await my_task.kiq(message.chat.id)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
