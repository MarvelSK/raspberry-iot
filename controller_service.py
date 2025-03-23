import time


class ControllerService:
    def __init__(self, supabase_handler, gpio_handler, controller_id):
        self.supabase = supabase_handler
        self.gpio = gpio_handler
        self.controller_id = controller_id
        self.devices = {}

    def initialize(self):
        asyncio.run(self.supabase.update_controller_status(is_online=True))
        self.devices = asyncio.run(self.supabase.get_controller_devices())

        for device in self.devices.values():
            if device.get('gpio_pin'):
                self.gpio.setup_pin(device)

        print(f"Initialized {len(self.devices)} devices")

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
                    asyncio.run(self.supabase.update_device_value(device_id, value))

    def update_controller_status(self):
        asyncio.run(self.supabase.update_controller_status(last_seen=time.time()))

    def check_connection(self):
        connected = asyncio.run(self.supabase.check_connection())
        if not connected:
            print("Reconnecting to Supabase...")
            asyncio.run(self.supabase.reconnect())
            asyncio.run(self.subscribe_to_device_changes())

    def cleanup(self):
        asyncio.run(self.supabase.update_controller_status(is_online=False))
