from __future__ import annotations

from typing import Callable

from bootstrap.runtime_registrations import register_gui_runtime, runtime_factories
from core.context import AppContext
from model.app_config import load_runtime_config


def build_gui_context(*, view, log: Callable[[str], None], post: Callable[[Callable[[], None]], None]) -> AppContext:
    config = load_runtime_config()

    register_gui_runtime(view=view, log=log, post=post, config=config)
    service_factories, controller_factories = runtime_factories()

    state = {"config": config}
    return AppContext(
        state=state,
        service_factories=service_factories,
        controller_factories=controller_factories,
    )
