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
from aiogram import Bot, Dispatcher, executor
# Your taskiq broker
from your_project.tkq import broker


bot = Bot(token="API_TOKEN")

dispatcher = Dispatcher(bot)


async def setup_taskiq(_: Dispatcher):
    # Here we check if it's a clien-side,
    # Becuase otherwise you're going to
    # create infinite loop of startup events.
    if not broker.is_worker_process:
        print("Setting up taskiq")
        await broker.startup()


async def shutdown_taskiq(_: Dispatcher):
    if not broker.is_worker_process:
        print("Shutting down taskiq")
        await broker.shutdown()

# Here we defined our executor.
bot_executor = executor.Executor(dispatcher=dispatcher)
bot_executor.on_startup([setup_taskiq])
bot_executor.on_shutdown([shutdown_taskiq])

if __name__ == "__main__":
    bot_executor.start_polling()

```

The only thing that left is to add one line to your broker definition.


```python
# Please use real broker for taskiq.
from taskiq_broker import MyBroker
import taskiq_aiogram

broker = MyBroker()

# This line is going to initialize everything.
taskiq_aiogram.init(
    broker,
    # Here we define path to your executor.
    # This format is similar to uvicorn or gunicorn.
    "your_project.__main__:bot_executor",
    pooling=True,
    webhook=False,
)
```

Aiogram defines startup events for pooling and webhooks separately. So you need to
explicitly specify which mode suites you. BTW, by default aiogram adds handler events to
both, so setting only pooling to True should be enought for almost any case.

That's it.

Let's create some tasks!

```python
# Sometimes python imports wrong task names.
# If that happens, please set a task_name explicitly.
@broker.task(task_name="my_task")
async def my_task(chat_id: int, bot: Bot = TaskiqDepends()) -> None:
    print("I'm a task")
    await asyncio.sleep(4)
    await bot.send_message(chat_id, "task completed")


@dispatcher.message_handler(commands=["task"])
async def send_task(message: types.Message):
    await message.reply("Sending a task")
    await my_task.kiq(message.chat.id)

```

And it works!

![Showcase.jpg](https://raw.githubusercontent.com/taskiq-python/taskiq-aiogram/master/imgs/showcase.jpg)
