from __future__ import annotations

from typing import Any, Callable


class AppContext:
    """Small runtime context with lazy service/controller registries."""

    def __init__(
        self,
        *,
        state: dict[str, Any] | None = None,
        service_factories: dict[str, Callable[["AppContext"], Any]] | None = None,
        controller_factories: dict[str, Callable[["AppContext"], Any]] | None = None,
    ) -> None:
        self.state = state or {}
        self._service_factories = service_factories or {}
        self._controller_factories = controller_factories or {}
        self._services: dict[str, Any] = {}
        self._controllers: dict[str, Any] = {}

    def service(self, key: str) -> Any:
        name = str(key or "").strip()
        if name in self._services:
            return self._services[name]

        factory = self._service_factories.get(name)
        if factory is None:
            raise KeyError(f"Unknown service: {name}")

        instance = factory(self)
        self._services[name] = instance
        return instance

    def controller(self, key: str) -> Any:
        name = str(key or "").strip()
        if name in self._controllers:
            return self._controllers[name]

        factory = self._controller_factories.get(name)
        if factory is None:
            raise KeyError(f"Unknown controller: {name}")

        instance = factory(self)
        self._controllers[name] = instance
        return instance
