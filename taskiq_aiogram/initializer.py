from typing import Awaitable, Callable

from aiogram import Bot, Dispatcher, executor
from taskiq import AsyncBroker, TaskiqEvents, TaskiqState
from taskiq.cli.utils import import_object

POOLING_MODE_KEY = "aiogram_pooling_mode"
WEBHOOK_MODE_KEY = "aiogram_webhook_mode"
EXECUTOR_KEY = "aiogram_executor"


def startup_event_generator(
    broker: AsyncBroker,
    user_executor: executor.Executor,
    pooling: bool,
    webhook: bool,
) -> Callable[[TaskiqState], Awaitable[None]]:
    """
    Generate startup event for broker.

    :param broker: current broker.
    :param user_executor: imported executor.
    :param pooling: pooling mode enabled.
    :param webhook: webhook mode enabled.
    :return: callable event handler.
    """

    async def startup(state: TaskiqState) -> None:
        user_executor.skip_updates = False
        if pooling:
            await user_executor._startup_polling()
        if webhook:
            await user_executor._startup_webhook()

        broker.add_dependency_context(
            {
                executor.Executor: user_executor,
                Dispatcher: user_executor.dispatcher,
                Bot: user_executor.dispatcher.bot,
            },
        )
        state[EXECUTOR_KEY] = user_executor
        state[POOLING_MODE_KEY] = user_executor
        state[WEBHOOK_MODE_KEY] = user_executor

    return startup


async def shutdown(state: TaskiqState) -> None:
    """
    This function is used to shutdown broker properly.

    :param state: current state.
    """
    user_executor: "executor.Executor" = state["aiogram_executor"]
    if state[POOLING_MODE_KEY]:
        await user_executor._shutdown_polling()
    if state[WEBHOOK_MODE_KEY]:
        await user_executor._shutdown_polling()


def init(
    broker: AsyncBroker,
    executor_path: str,
    pooling: bool = True,
    webhook: bool = False,
) -> None:
    """
    Initialize taskiq broker.

    This function creates startup
    and shutdown events handlers,
    that trigger executor's startup and shutdown events.

    After this function is called, dispatcher and bot
    are going to be available in your tasks,
    using TaskiqDepends.

    :param broker: current broker.
    :param executor_path: path to your executor.
    :param pooling: whether you want to start a bot in pooling mode.
    :param webhook: whether you want to start a bot in webhook mode.
    :raises ValueError: raised if you passed a path not to an executor object.
    """
    if not broker.is_worker_process:
        return

    user_executor = import_object(executor_path)
    if not isinstance(user_executor, executor.Executor):
        raise ValueError(f"{executor_path} is not an Executor instance.")

    broker.add_event_handler(
        TaskiqEvents.WORKER_STARTUP,
        startup_event_generator(
            broker,
            user_executor,
            pooling,
            webhook,
        ),
    )
    broker.add_event_handler(
        TaskiqEvents.WORKER_SHUTDOWN,
        shutdown,
    )
