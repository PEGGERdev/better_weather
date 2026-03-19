from __future__ import annotations

import unittest

from bootstrap.app_bootstrap import build_gui_context


class _FakeView:
    def set_status(self, _text: str) -> None:
        return None

    def set_running_state(self, _running: bool) -> None:
        return None

    def append_log(self, _line: str) -> None:
        return None

    def set_telemetry_mode(self, _text: str) -> None:
        return None

    def update_weather(self, _payload: dict) -> None:
        return None

    def update_ossd(self, _st: tuple) -> None:
        return None

    def chart_add_ossd(self, _channel_idx: int, _ts, _label: str) -> None:
        return None

    def chart_redraw(self) -> None:
        return None


class BootstrapRuntimeTests(unittest.TestCase):
    def test_build_gui_context_rebinds_runtime_factories(self) -> None:
        view_a = _FakeView()
        view_b = _FakeView()

        ctx_a = build_gui_context(view=view_a, log=lambda _msg: None, post=lambda fn: fn())
        ctrl_a = ctx_a.controller("app")

        ctx_b = build_gui_context(view=view_b, log=lambda _msg: None, post=lambda fn: fn())
        ctrl_b = ctx_b.controller("app")

        self.assertIs(ctrl_a._v, view_a)
        self.assertIs(ctrl_b._v, view_b)
        self.assertIsNot(ctrl_a, ctrl_b)


if __name__ == "__main__":
    unittest.main()
