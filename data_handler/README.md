# Data Handler Service

Standalone service that manages USB connections to the Arduino (OSSD) and weather station hardware.

## Usage

### Standalone (Backend Mode)

Run the data handler as a standalone service that sends data directly to the backend API:

```bash
# Using environment variables
DATA_HANDLER_OUTPUT=backend BACKEND_BASE=http://127.0.0.1:8000 python data_handler_service.py

# Or with default settings (backend mode)
python data_handler_service.py
```

### IPC Mode (for Python Frontend)

Run the data handler in IPC mode to output JSON to stdout:

```bash
DATA_HANDLER_OUTPUT=ipc python data_handler_service.py
```

The service will output JSON lines to stdout:
- OSSD events: `{"type":"ossd","ts":"2026-01-01T12:00:00+00:00","lichtgitterNr":1,"ossdNr":2,"status":"E"}`
- Weather readings: `{"type":"weather","ts":"2026-01-01T12:00:00+00:00","temp":18.5,"pressure":1008.2,...}`

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SERIAL_PORT` | `/dev/ttyACM0` | Arduino serial port |
| `SERIAL_BAUD` | `9600` | Serial baud rate |
| `HID_VID` | `0x1941` | Weather station USB VID |
| `HID_PID` | `0x8021` | Weather station USB PID |
| `DATA_HANDLER_POLL_SEC` | `0.2` | OSSD poll interval in seconds |
| `DATA_HANDLER_INTERVAL_SEC` | `30.0` | Weather read interval in seconds |
| `BACKEND_BASE` | `http://127.0.0.1:8000` | Backend API base URL |
| `DATA_HANDLER_OUTPUT` | `backend` | Output mode: `backend` or `ipc` |
| `DATA_HANDLER_LOG_LEVEL` | `INFO` | Log level (`DEBUG`, `INFO`) |

### Weather Station Calibration

| Variable | Default | Description |
|----------|---------|-------------|
| `WEATHER_DEBUG` | `0` | Enable debug logging |
| `WEATHER_PTR_SWAP` | `0` | Swap pointer bytes |
| `WEATHER_TEMP_SCALE` | `0.1` | Temperature scaling factor |
| `WEATHER_PRESSURE_SCALE` | `0.1` | Pressure scaling factor |
| `WEATHER_WIND_SCALE` | `0.1` | Wind speed scaling factor |
| `WEATHER_RAIN_FACTOR` | `0.3` | Rain factor |
| `WEATHER_LIGHT_DIV` | `10` | Light divisor |

## Integration with Python Frontend (Legacy)

The Qt/Python frontend is kept for compatibility only. New product work targets backend + web frontend.

The Python frontend can spawn the data handler as a subprocess:

```python
from model.data_handler_subprocess import DataHandlerSubprocess

handler = DataHandlerSubprocess(
    serial_port="/dev/ttyACM0",
    hid_vid=0x1941,
    hid_pid=0x8021,
    on_ossd=lambda entry: print(f"OSSD: {entry}"),
    on_weather=lambda weather: print(f"Weather: {weather}"),
    on_log=lambda msg: print(f"Log: {msg}"),
)

handler.start()
# ... later
handler.stop()
```

Or use the environment variable:

```bash
DATA_HANDLER_SUBPROCESS=1 python -m witterungsstation_py.main
```

## Testing

Run the data handler tests:

```bash
python -m unittest data_handler.tests.test_handler -v
```
