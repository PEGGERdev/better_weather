from __future__ import annotations

"""
Data Handler Core Service.

Manages USB connections to Arduino (OSSD) and weather station.
Uses shared generic services for serial, HID, and configuration.
"""

import signal
from typing import Callable, Optional

from data_handler.contracts import BaseLifecycleService, BaseOssdReader, BaseOutputHandler, BaseWeatherReader
from data_handler.orchestrator import PipelineOrchestrator
from data_handler.outputs.backend_output import BackendOutputHandler
from data_handler.outputs.composite_output import CompositeOutputHandler
from data_handler.outputs.ipc_output import IpcOutputHandler
from data_handler.readers.ossd_reader import OssdReader
from data_handler.readers.weather_reader import WeatherReader
from shared.config import DataHandlerConfig, load_data_handler_config
from shared.logging import LogGateway
from shared.serial_client import SerialClient, SerialConfig
from shared.hid_client import HidClient, HidConfig
from shared.parsers import OssdParser, WeatherParser
from data_handler.registry import get_service, register_service


@register_service(kind="lifecycle", name="pipeline")
class DataHandler(BaseLifecycleService):
    def __init__(
        self,
        config: Optional[DataHandlerConfig] = None,
        output: Optional[BaseOutputHandler] = None,
        log: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._config = config or load_data_handler_config()
        self._log_gateway = LogGateway("data_handler", self._config.logging.level)
        if log:
            self._log_gateway.set_callback(log)
        self._log = self._log_gateway

        self._output = output or self._create_output()

        self._serial_client: Optional[SerialClient] = None
        self._hid_client: Optional[HidClient] = None
        self._ossd_reader: Optional[BaseOssdReader] = None
        self._weather_reader: Optional[BaseWeatherReader] = None
        self._pipeline: Optional[PipelineOrchestrator] = None
        
        self._ossd_parser = OssdParser()
        self._weather_parser = WeatherParser(self._log)

    def _create_output(self) -> BaseOutputHandler:
        if self._config.output_mode == "both":
            return CompositeOutputHandler(
                BackendOutputHandler(self._config.backend.base_url, self._log),
                IpcOutputHandler(self._log),
            )
        output_cls = get_service("output", self._config.output_mode)
        if self._config.output_mode == "backend":
            return output_cls(self._config.backend.base_url, self._log)
        return output_cls(self._log)

    def _setup_signal_handlers(self) -> None:
        def handle_sigterm(signum, frame):
            _ = frame
            self._log(f"DataHandler received signal {signum}, shutting down")
            if self._pipeline:
                self._pipeline.stop()

        try:
            signal.signal(signal.SIGTERM, handle_sigterm)
            signal.signal(signal.SIGINT, handle_sigterm)
        except Exception:
            pass

    def _open_serial(self) -> bool:
        serial_config = SerialConfig(
            port=self._config.serial.port,
            baud=self._config.serial.baud,
            timeout=1.0,
        )
        self._serial_client = SerialClient(serial_config, self._log)
        is_open = self._serial_client.open()
        if is_open:
            reader_cls = get_service("reader", "ossd")
            self._ossd_reader = reader_cls(
                serial_client=self._serial_client,
                parser=self._ossd_parser,
                log=self._log,
                debug=self._config.logging.level == "DEBUG",
            )
        return is_open

    def _open_hid(self) -> bool:
        hid_config = HidConfig(
            vid=self._config.hid.vid,
            pid=self._config.hid.pid,
            report_size=32,
        )
        self._hid_client = HidClient(hid_config, self._log)
        is_open = self._hid_client.open()
        if is_open:
            reader_cls = get_service("reader", "weather")
            self._weather_reader = reader_cls(
                hid_client=self._hid_client,
                parser=self._weather_parser,
                log=self._log,
            )
        return is_open

    def run(self) -> None:
        self._setup_signal_handlers()

        self._log(
            f"DataHandler starting: mode={self._config.output_mode} "
            f"serial={self._config.serial.port} "
            f"hid=0x{self._config.hid.vid:04X}:0x{self._config.hid.pid:04X}"
        )

        serial_ok = self._open_serial()
        hid_ok = False
        if self._config.disable_weather:
            self._log("DataHandler: weather reader disabled by config")
        else:
            hid_ok = self._open_hid()

        if not serial_ok and not hid_ok:
            self._log("DataHandler: no sensors available, exiting")
            return

        self._pipeline = PipelineOrchestrator(
            ossd_reader=self._ossd_reader,
            weather_reader=self._weather_reader,
            output=self._output,
            poll_sec=self._config.poll_sec,
            weather_interval_sec=self._config.interval_sec,
            log=self._log,
        )
        self._pipeline.run()

        self._log("DataHandler stopped")

    def stop(self) -> None:
        if self._pipeline:
            self._pipeline.stop()

    def close(self) -> None:
        if self._pipeline:
            self._pipeline.close()
            self._pipeline = None
        if self._serial_client:
            self._serial_client.close()
            self._serial_client = None
        if self._hid_client:
            self._hid_client.close()
            self._hid_client = None
        self._output.close()
