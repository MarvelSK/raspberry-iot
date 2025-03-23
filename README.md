
---

# Raspberry Pi Supabase Controller

This project allows a Raspberry Pi to communicate with Supabase to control GPIO pins based on device status stored in the database.

## Logging options

- "DEBUG" - Shows all detailed information (very verbose)  
- "INFO" - Shows general operational information (default)  
- "WARNING" - Shows warnings and errors only  
- "ERROR" - Shows only errors  
- "CRITICAL" - Shows only critical errors  

## Features

- Connect to Supabase and identify as a specific control unit  
- Control GPIO pins based on device states in the database  
- Report sensor readings back to Supabase  
- Update system metrics (CPU, memory, storage usage)  
- Real-time updates using Supabase realtime subscriptions  

## Installation

### 1. Update and upgrade Raspberry Pi OS

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Python 3 and required tools

```bash
sudo apt install python3 python3-pip python3-venv git -y
```

### 3. Clone this repository

```bash
git clone https://github.com/MarvelSK/raspberry-iot.git
cd raspberry-iot
```

### 4. Create and activate Python virtual environment

```bash
python3 -m venv controller
source controller/bin/activate
```

### 5. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 6. Set up environment variables

```bash
cp .env.example .env
nano .env
```

Fill in your Supabase details:

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
CONTROL_UNIT_ID=your-control-unit-id
```

Save and exit (`Ctrl + X`, `Y`, `Enter`).

### 7. Test the controller manually

```bash
python main.py
```

## Setting up as a Service

To ensure the controller runs automatically at startup:

### 1. Create a systemd service

```bash
sudo nano /etc/systemd/system/raspberry-iot.service
```

### 2. Add this content:

```
[Unit]
Description=Raspberry Pi Supabase Controller
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/raspberry-iot
ExecStart=/home/pi/raspberry-iot/controller/bin/python /home/pi/raspberry-iot/main.py
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

Save and exit.

### 3. Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable raspberry-iot.service
sudo systemctl start raspberry-iot.service
```

### 4. Check service status

```bash
sudo systemctl status raspberry-iot.service
```

### 5. View logs for troubleshooting

```bash
tail -f controller.log
```

## Adding Devices in Supabase

1. Add a device in the `devices` table with necessary details.  
2. Link it to your control unit in the `control_units_devices` table.  
3. Ensure the `gpio_pin` field is set to the GPIO BCM pin number you wish to use.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---