# Taskiq + Aiogram

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/taskiq-aiogram?style=for-the-badge)](https://pypi.org/project/taskiq-aiogram/)
[![PyPI](https://img.shields.io/pypi/v/taskiq-aiogram?style=for-the-badge)](https://pypi.org/project/taskiq-aiogram/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/taskiq-aiogram?style=for-the-badge)](https://pypistats.org/packages/taskiq-aiogram)

This repo adds integration between your aiogram application and taskiq.

It runs all startup and shutdown events of your application and adds 3 dependencies,
that you can use in your tasks.

1. Executor - your executor;
2. Dispatcher - that were used along with executor;
3. Bot - your bot instance.

## Usage

Add an executor to your main file and make it possible to available for import.
By default AioGram hides the way it creates executor, but since we want to use
startup and shutdown events, you have to manually define your executor.

For example:

```python
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher

# Your taskiq broker
from your_project.tkq import broker

dp = Dispatcher()
bot = Bot(token="TOKEN")


@dp.startup()
async def setup_taskiq(bot: Bot, *_args, **_kwargs):
    # Here we check if it's a clien-side,
    # Becuase otherwise you're going to
    # create infinite loop of startup events.
    if not broker.is_worker_process:
        logging.info("Setting up taskiq")
        await broker.startup()


@dp.shutdown()
async def shutdown_taskiq(bot: Bot, *_args, **_kwargs):
    if not broker.is_worker_process:
        logging.info("Shutting down taskiq")
        await broker.shutdown()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

```

The only thing that left is to add few lines to your broker definition.


```python
# Please use real broker for taskiq.
from taskiq_broker import MyBroker
import taskiq_aiogram

broker = MyBroker()

# This line is going to initialize everything.
taskiq_aiogram.init(
    broker,
    "your_project.__main__:dp",
    "your_project.__main__:bot",
)
```

That's it.

Let's create some tasks! I created task in a separate module,
named `tasks.py`.

```python
from aiogram import Bot
from your_project.tkq import broker

@broker.task(task_name="my_task")
async def my_task(chat_id: int, bot: Bot = TaskiqDepends()) -> None:
    print("I'm a task")
    await asyncio.sleep(4)
    await bot.send_message(chat_id, "task completed")

```

Now let's call our new task somewhere in bot commands.

```python
from aiogram import types
from aiogram.filters import Command

from tasks import my_task


@dp.message(Command("task"))
async def message(message: types.Message):
    await my_task.kiq(message.chat.id)

```

To start the worker, please type:

```
taskiq worker your_project.tkq:broker --fs-discover
```

We use `--fs-discover` to find all tasks.py modules recursively
and import all tasks into broker.


Now we can fire the task and see everything in action.

![Showcase.jpg](https://raw.githubusercontent.com/taskiq-python/taskiq-aiogram/master/imgs/showcase.jpg)
