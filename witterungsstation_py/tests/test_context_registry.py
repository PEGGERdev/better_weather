from __future__ import annotations

import unittest

from core.context import AppContext


class ContextRegistryTests(unittest.TestCase):
    def test_services_and_controllers_are_lazy_singletons(self) -> None:
        calls = {"service": 0, "controller": 0}

        class ServiceA:
            pass

        class ControllerA:
            def __init__(self, service: ServiceA) -> None:
                self.service = service

        ctx = AppContext(
            state={"name": "test"},
            service_factories={
                "serviceA": lambda _ctx: calls.__setitem__("service", calls["service"] + 1) or ServiceA(),
            },
            controller_factories={
                "controllerA": lambda context: calls.__setitem__("controller", calls["controller"] + 1)
                or ControllerA(context.service("serviceA")),
            },
        )

        a1 = ctx.service("serviceA")
        a2 = ctx.service("serviceA")
        c1 = ctx.controller("controllerA")
        c2 = ctx.controller("controllerA")

        self.assertIs(a1, a2)
        self.assertIs(c1, c2)
        self.assertIs(c1.service, a1)
        self.assertEqual(calls["service"], 1)
        self.assertEqual(calls["controller"], 1)


if __name__ == "__main__":
    unittest.main()
