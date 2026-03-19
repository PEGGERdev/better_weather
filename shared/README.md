# Shared Services

Centralized generic services used throughout the application.

## Modules

- `config.py` - Configuration loading from environment
- `logging.py` - Centralized logging with callbacks
- `serial_client.py` - Generic serial communication client
- `hid_client.py` - Generic HID communication client

## Usage

```python
from shared import (
    load_data_handler_config,
    load_app_config,
    SerialClient,
    HidClient,
    LogGateway,
)

# Configuration
config = load_data_handler_config()

# Logging
log = LogGateway("app", "INFO")

# Serial client
serial = SerialClient(
    SerialClientConfig(port="/dev/ttyACM0", baud=9600),
    log=log,
)
serial.open()
line = serial.query_line("G")
serial.close()

# HID client
hid = HidClient(
    HidClientConfig(vid=0x1941, pid=0x8021),
    log=log,
)
hid.open()
data = hid.query("A1 00 1E 20", 32)
hid.close()
```
