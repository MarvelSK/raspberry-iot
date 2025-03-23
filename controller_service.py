import time

class ControllerService:
    def __init__(self, supabase_handler, gpio_handler, controller_id):
        self.supabase = supabase_handler
        self.gpio = gpio_handler
        self.controller_id = controller_id
        self.devices = {}

    def initialize(self):
        self.supabase.update_controller_status(is_online=True)
        self.devices = self.supabase.get_controller_devices()
        for device in self.devices.values():
            gpio_pin = device.get('gpio_pin')
            if gpio_pin is not None and isinstance(gpio_pin, int):
                self.gpio.setup_pin(device)
            else:
                print(f"Invalid GPIO pin for device {device['id']}: {gpio_pin}")

        print(f"Initialized {len(self.devices)} devices.")

    async def subscribe_to_device_changes(self):
        await self.supabase.subscribe_to_devices(self.on_device_change)

    def on_device_change(self, payload):
        device_id = payload['new']['id']
        if device_id in self.devices:
            self.devices[device_id].update(payload['new'])
            if self.devices[device_id].get('gpio_pin'):
                self.gpio.update_pin_state(self.devices[device_id])

    def update_sensor_readings(self):
        for device_id, device in self.devices.items():
            if device['type'] == 'Senzor':
                value = self.gpio.read_sensor(device)
                if value is not None:
                    self.supabase.update_device_value(device_id, value)

    def update_controller_status(self):
        self.supabase.update_controller_status(last_seen=time.time())

    def check_connection(self):
        if not self.supabase.check_connection():
            self.supabase.reconnect()
            asyncio.run(self.subscribe_to_device_changes())

    def cleanup(self):
        self.supabase.update_controller_status(is_online=False)
