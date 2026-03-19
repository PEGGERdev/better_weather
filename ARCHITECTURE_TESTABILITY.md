# Architecture and Testability Standard

This project uses a **registry + composition root** architecture so every runtime component can be replaced by a test subclass and exercised without manual UI clicking.

Canonical product runtime is **backend + web frontend**.
The Qt runtime under `witterungsstation_py` is a legacy compatibility path and is no longer a first-class target for new feature work.

## Mandatory rules for new components

1. Implement a base contract (`Base*` abstract class / Protocol).
2. Register component using a registry decorator (`@register_*`).
3. Resolve component from composition root (no direct concrete `new` outside bootstrap).
4. Add a test subclass that inherits from the component and emits deterministic data.
5. Run full pipeline test through orchestrator (reader -> parser -> output -> API/frontend mapping).

## Registry map

- Backend: `backend/routing/registry.py`
- Shared parser registry: `shared/parser_registry.py`
- Data-handler service registry: `data_handler/registry.py`
- Frontend runtime registry: `frontend/src/core/runtimeRegistry.ts`

## Runtime orchestration

- Hardware ingestion is orchestrated by `data_handler/orchestrator.py`.
- Service entrypoint is `data_handler_service.py`.
- Output mode is selected by `DATA_HANDLER_OUTPUT=backend|ipc`.
- Canonical ingestion runtime is `data_handler`; legacy sender entrypoints are compatibility wrappers.

## No-click system testing

- Full stack smoke test:

```bash
python3 testbench/run_no_click_system_test.py
```

- Direct hardware weather station validation:

```bash
python3 testbench/run_direct_weather_station_test.py
```

- Frontend tests/build:

```bash
cd frontend && npm run test:run && npm run build
```

- Python tests:

```bash
cd witterungsstation_py && .venv/bin/python -m unittest discover -s tests -p "test_*.py"
cd .. && PYTHONPATH=. python3 -m unittest discover -s data_handler/tests -p "test_*.py"
```

## Test subclass pattern

Use inheritance, not ad-hoc monkey patches:

- Example: subclass `BaseWeatherReader` and override `read()` to return deterministic payload.
- Example: subclass `BaseOutputHandler` and capture emitted events to assert pipeline behavior.
