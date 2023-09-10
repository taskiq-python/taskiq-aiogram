import logging
from typing import Any, Awaitable, Callable, List

from aiogram import Bot, Dispatcher
from taskiq import AsyncBroker, TaskiqEvents, TaskiqState
from taskiq.cli.utils import import_object

BOT_KEY = "aiogram_bots"
WORKFLOW_KEY = "aiogram_workflow"
DISPATCHER_KEY = "aiogram_dispatcher"

logger = logging.getLogger("taskiq.taskiq_aiogram")


def startup_event_generator(  # noqa: C901
    broker: AsyncBroker,
    dispatcher_path: str,
    *bots_paths: str,
    **kwargs: str,
) -> Callable[[TaskiqState], Awaitable[None]]:
    """
    Generate startup event for broker.

    :param broker: current broker.
    :param dispatcher_path: python-path to the dispatcher object.
    :param bots_paths: python-paths to bots objects.
    :param kwargs: random key-word arguments.

    :returns: startup event handler.
    """

    async def startup(state: TaskiqState) -> None:
        if not broker.is_worker_process:
            return

        dispatcher = import_object(dispatcher_path)
        if not isinstance(dispatcher, Dispatcher):
            raise ValueError("Dispatcher should be an instance of dispatcher.")
        bots = []
        for bot_path in bots_paths:
            bot = import_object(bot_path)
            if not isinstance(bot, Bot):
                raise ValueError("Bots should be instances of Bot class.")
            bots.append(bot)

        workflow_data = {
            "dispatcher": dispatcher,
            "bots": bots,
            **dispatcher.workflow_data,
            **kwargs,
        }
        if "bot" in workflow_data:
            workflow_data.pop("bot")

        state[BOT_KEY] = bots
        state[WORKFLOW_KEY] = workflow_data
        state[DISPATCHER_KEY] = dispatcher

        await dispatcher.emit_startup(bot=bots[-1], **workflow_data)

        broker.add_dependency_context(
            {
                Dispatcher: dispatcher,
                Bot: bots[-1],
                List[Bot]: bots,
            },
        )

    return startup


def shutdown_event_generator(
    broker: AsyncBroker,
) -> Callable[[TaskiqState], Awaitable[None]]:
    """
    Generate shutdown event for broker.

    This function doesn't take any parameters,
    except broker,
    because all needed information for shutdown
    can be obtained from the state.

    :param broker: current broker.

    :returns: shutdown event handler.
    """

    async def shutdown(state: TaskiqState) -> None:
        if not broker.is_worker_process:
            return
        bots: List[Bot] = state[BOT_KEY]
        workflow_data: dict[str, Any] = state[WORKFLOW_KEY]
        dispatcher: Dispatcher = state[DISPATCHER_KEY]

        try:
            await dispatcher.emit_shutdown(bots[-1], **workflow_data)
        except Exception as exc:
            logger.warn(f"Error found while shutting down: {exc}")

    return shutdown


def init(
    broker: AsyncBroker,
    dispatcher: str,
    bot: str,
    *other_bots: str,
    **kwargs: Any,
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
    :param dispatcher: python-path to the dispatcher.
    :param bot: bot to use.
    :param other_bots: python-paths to other bots.
    :param kwargs: random key-word arguments for shutdown and startup events.
    """
    broker.add_event_handler(
        TaskiqEvents.WORKER_STARTUP,
        startup_event_generator(
            broker,
            dispatcher,
            bot,
            *other_bots,
            **kwargs,
        ),
    )
    broker.add_event_handler(
        TaskiqEvents.WORKER_SHUTDOWN,
        shutdown_event_generator(broker),
    )
