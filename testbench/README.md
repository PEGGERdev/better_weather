## Testbench (No-Click)

This directory provides command-driven end-to-end tests so the full application can be validated without manual UI interaction.

### Goals

- Start required runtime components automatically.
- Ingest real hardware data through the generic data-handler pipeline.
- Verify backend state changes (`/weather/`, `/ossd/`).
- Keep tests reproducible and CI-friendly.

### Run full no-click smoke test

```bash
python3 testbench/run_no_click_system_test.py
```

This includes a **direct weather station read** check before the pipeline smoke run.

### Run direct weather station check only

```bash
python3 testbench/run_direct_weather_station_test.py
```

### Run automated frontend and python tests

```bash
cd frontend && npm run test:run && npm run build
cd ../witterungsstation_py && .venv/bin/python -m unittest discover -s tests -p "test_*.py"
cd .. && witterungsstation_py/.venv/bin/python -m unittest data_handler.tests.test_handler
```

### Architecture rule

Any new component must:

1. Implement a base contract (`Base*` class / Protocol).
2. Register itself through a registry decorator.
3. Be resolvable by kind+name from composition root.
4. Include a test subclass in tests that runs through the pipeline.
