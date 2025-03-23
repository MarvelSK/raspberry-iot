import time


class ControllerService:
    def __init__(self, supabase_handler, gpio_handler, controller_id):
        self.supabase = supabase_handler
        self.gpio = gpio_handler
        self.controller_id = controller_id
        self.devices = {}

    def initialize(self):
        """
        Initialize the controller by updating its status and setting up devices.
        """
        self.supabase.update_controller_status(is_online=True)
        self.devices = self.supabase.get_controller_devices()
        for device in self.devices.values():
            if device.get('gpio_pin') is not None:
                self.gpio.setup_pin(device)
        print(f"Initialized {len(self.devices)} devices")

    async def subscribe_to_device_changes(self):
        """
        Subscribe to device change events asynchronously.
        """
        await self.supabase.subscribe_to_devices(self.on_device_change)

    async def on_device_change(self, payload):
        """
        Handle device state changes received from Supabase.

        Parameters:
            payload (dict): The data payload containing device changes.
        """
        device_id = payload['new']['id']
        if device_id in self.devices:
            self.devices[device_id].update(payload['new'])
            if self.devices[device_id].get('gpio_pin') is not None:
                self.gpio.update_pin_state(self.devices[device_id])
            print(f"Device {device_id} updated: {self.devices[device_id]}")

    def update_sensor_readings(self):
        """
        Read sensor values and update them in Supabase.
        """
        for device_id, device in self.devices.items():
            if device['type'] == 'Senzor':
                value = self.gpio.read_sensor(device)
                if value is not None:
                    self.supabase.update_device_value(device_id, value)
                    print(f"Sensor {device_id} value updated: {value}")

    def update_controller_status(self):
        """
        Update controller's last seen status in Supabase.
        """
        self.supabase.update_controller_status(last_seen=time.time())
        print("Controller status updated.")

    async def check_connection(self):
        """
        Check Supabase connection and reconnect if needed.
        """
        if not self.supabase.check_connection():
            print("Reconnecting to Supabase...")
            self.supabase.reconnect()
            await self.subscribe_to_device_changes()

    def cleanup(self):
        """
        Cleanup resources and update controller status when shutting down.
        """
        self.supabase.update_controller_status(is_online=False)
        print("Controller cleanup complete. Controller marked offline.")
