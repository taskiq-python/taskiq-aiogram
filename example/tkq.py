from taskiq_redis import ListQueueBroker

from taskiq_aiogram import init

broker = ListQueueBroker("redis://localhost")

init(
    broker,
    "example.__main__:dp",
    "example.__main__:bot",
)
