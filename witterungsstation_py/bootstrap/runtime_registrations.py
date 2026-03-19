from __future__ import annotations

from core.runtime_registry import (
    get_controller_factories,
    get_service_factories,
    register_controller_factory,
    register_service_factory,
    reset_runtime_registry,
    validate_runtime_registry,
)
from controller.live_runtime_controller import LiveRuntimeController
from model.data_handler_subprocess import DataHandlerSubprocess
from model.db_client import DbClient
from model.system_clock import SystemClock


def register_gui_runtime(*, view, log, post, config) -> None:
    reset_runtime_registry()

    register_service_factory("clock", lambda _ctx: SystemClock())
    register_service_factory("telemetry", lambda _ctx: DbClient(config.backend_base, log=log))
    register_service_factory("weatherLiveReader", lambda _ctx: None)
    register_service_factory(
        "dataHandlerSubprocess",
        lambda _ctx: DataHandlerSubprocess(
            serial_port=config.serial_port,
            serial_baud=config.serial_baud,
            hid_vid=config.hid_vid,
            hid_pid=config.hid_pid,
            poll_sec=config.poll_sec,
            interval_sec=config.interval_sec,
            backend_base=config.backend_base,
            output_mode="ipc",
            disable_weather=False,
            on_log=log,
        ),
    )

    register_controller_factory(
        "app",
        lambda ctx: LiveRuntimeController(
            view=view,
            model_db=ctx.service("telemetry"),
            data_handler=ctx.service("dataHandlerSubprocess"),
            weather_live_reader=ctx.service("weatherLiveReader"),
            poll_sec=config.poll_sec,
            backend_interval_sec=config.interval_sec,
            post=post,
        ),
    )

    validate_runtime_registry(
        required_services=["clock", "telemetry", "weatherLiveReader", "dataHandlerSubprocess"],
        required_controllers=["app"],
    )

def runtime_factories() -> tuple[dict, dict]:
    return get_service_factories(), get_controller_factories()


def reset_runtime_registration_state() -> None:
    reset_runtime_registry()
