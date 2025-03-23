# Raspberry Pi Supabase Controller

This project allows a Raspberry Pi to communicate with Supabase to control GPIO pins based on device status stored in the database.

## Features

- Connect to Supabase and identify as a specific control unit
- Control GPIO pins based on device states in the database
- Report sensor readings back to Supabase
- Update system metrics (CPU, memory, storage usage)
- Real-time updates using Supabase realtime subscriptions

## Installation

1. Clone this repository onto your Raspberry Pi:

```bash
git clone https://github.com/yourusername/rpi-supabase-controller.git
cd rpi-supabase-controller
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on the `.env.example` template:

```bash
cp .env.example .env
```

4. Edit the `.env` file and fill in your Supabase URL, API key, and Control Unit ID:

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
CONTROL_UNIT_ID=your-control-unit-id
```

## Usage

Run the controller:

```bash
python main.py
```

The controller will:

1. Connect to Supabase and set the control unit status to online
2. Fetch all devices associated with this control unit
3. Set up GPIO pins according to the device configuration
4. Listen for real-time updates to device states
5. Periodically report system metrics back to Supabase

## Adding Devices in Supabase

To add a device that will be controlled by this Raspberry Pi:

1. Create a new device in the `devices` table
2. Link the device to your control unit in the `control_units_devices` table
3. Make sure to set the `gpio_pin` field to the GPIO BCM pin number you want to use

## Setting up as a Service

To run the controller automatically at startup, you can set it up as a systemd service.

1. Create a service file:

```bash
sudo nano /etc/systemd/system/rpi-supabase-controller.service
```

2. Add the following content:

```
[Unit]
Description=Raspberry Pi Supabase Controller
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/rpi-supabase-controller
ExecStart=/usr/bin/python3 /home/pi/rpi-supabase-controller/main.py
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```bash
sudo systemctl enable rpi-supabase-controller.service
sudo systemctl start rpi-supabase-controller.service
```

4. Check the status:

```bash
sudo systemctl status rpi-supabase-controller.service
```

## Troubleshooting

Check the logs for any errors:

```bash
tail -f controller.log
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.