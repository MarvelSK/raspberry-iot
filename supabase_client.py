import platform
import socket
import threading
import time
import uuid
from datetime import datetime, UTC

from supabase import create_client, Client
from w1thermsensor import W1ThermSensor

from config import SUPABASE_URL, SUPABASE_KEY, CONTROL_UNIT_ID, logger
from system_monitor import SystemMonitor


class SupabaseManager:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL and API key must be set in .env file")

        if not CONTROL_UNIT_ID:
            raise ValueError("Control unit ID must be set in .env file")

        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.control_unit_id = CONTROL_UNIT_ID
        self.connected = False
        self.keep_alive_thread = None  # Thread for updating is_online
        logger.info(f"Initialized Supabase client for control unit: {self.control_unit_id}")

    def get_system_info(self):
        """Retrieve system information (runs once at startup)"""
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
            mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 8)][::-1])
            firmware = platform.release()
            model = platform.machine()

            return {
                "ip_address": ip_address,
                "mac_address": mac_address,
                "firmware": firmware,
                "model": model
            }
        except Exception as e:
            logger.error(f"Failed to retrieve system info: {e}")
            return {}

    def update_system_info(self):
        """Update Supabase with system information (runs once at startup)"""
        try:
            system_info = self.get_system_info()
            if system_info:
                self.supabase.table("control_units").update(system_info).eq("id", self.control_unit_id).execute()
                logger.info(f"Updated system info: {system_info}")
        except Exception as e:
            logger.error(f"Failed to update system info: {e}")

    def connect(self):
        """Update control unit status to online and start metrics updates"""
        try:
            # Update system information once on startup
            self.update_system_info()

            # Mark as online
            self.supabase.table("control_units").update({
                "is_online": True,
                "last_seen": datetime.now(UTC).isoformat(),
                "cpu_usage": 0,
                "memory_usage": 0,
                "storage_usage": 0
            }).eq("id", self.control_unit_id).execute()

            logger.info(f"Control unit {self.control_unit_id} is now online")
            self.connected = True

            # Start background thread to keep metrics updated
            self.keep_alive_thread = threading.Thread(target=self.keep_alive, daemon=True)
            self.keep_alive_thread.start()

            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            self.connected = False
            return False

    # In SupabaseManager, update the `keep_alive` method:
    def keep_alive(self):
        """Continuously update metrics every 60 seconds"""
        system_monitor = SystemMonitor()  # Create an instance of SystemMonitor
        while self.connected:
            try:
                # Use SystemMonitor to get metrics
                metrics = system_monitor.get_metrics()

                update_data = {
                    "cpu_usage": metrics["cpu_usage"],
                    "memory_usage": metrics["memory_usage"],
                    "storage_usage": metrics["storage_usage"],
                    "is_online": True,
                    "last_seen": datetime.now(UTC).isoformat()
                }

                self.supabase.table("control_units").update(update_data).eq("id", self.control_unit_id).execute()
                logger.debug(f"Updated control unit metrics: {update_data}")

            except Exception as e:
                logger.error(f"Failed to update control unit metrics: {e}")

            time.sleep(60)  # Wait 60 seconds before next update

    def disconnect(self):
        """Update control unit status to offline"""
        if not self.connected:
            return

        try:
            self.supabase.table("control_units").update({
                "is_online": False,
                "last_seen": datetime.now(UTC).isoformat()
            }).eq("id", self.control_unit_id).execute()

            logger.info(f"Control unit {self.control_unit_id} is now offline")
            self.connected = False
        except Exception as e:
            logger.error(f"Failed to update offline status: {e}")

    def get_devices(self):
        """Get devices associated with this control unit using the new controller_id field"""
        try:
            response = self.supabase.table("devices").select("*").eq(
                "controller_id", self.control_unit_id
            ).execute()

            if isinstance(response, dict) and "data" in response:
                devices = response["data"]
                logger.info(f"Retrieved {len(devices)} devices for control unit")
                return devices
            else:
                logger.warning("No data returned when fetching devices")
                return []
        except Exception as e:
            logger.error(f"Failed to fetch devices: {e}")
            return []

    def read_ds18b20(self, gpio_pin=4):
        """Read temperature from DS18B20 sensor."""
        sensor = W1ThermSensor()
        temperature = sensor.get_temperature()
        logger.info(f"DS18B20 Temperature: {temperature}°C")
        return temperature

    def update_sensor_data(self, device_id, temperature=None, humidity=None):
        """Update sensor data in Supabase."""
        try:
            update_data = {
                "last_updated": datetime.now(UTC).isoformat(),
            }
            if temperature is not None:
                update_data["value"] = temperature  # or store as separate temperature/humidity columns
                update_data["unit"] = "°C"
            if humidity is not None:
                update_data["value"] = humidity  # if you want to store humidity separately
                update_data["unit"] = "%"

            response = self.supabase.table("devices").update(update_data).eq("id", device_id).execute()
            logger.info(f"Updated sensor {device_id} data: temperature={temperature}, humidity={humidity}")
        except Exception as e:
            logger.error(f"Failed to update sensor data for {device_id}: {e}")

    def check_and_send_sensor_data(self):
        """Check devices and send sensor data to Supabase if applicable."""
        try:
            devices = self.get_devices()

            if devices:
                for device in devices:
                    # Check if the device is a temperature sensor with '°C' as the unit and has a GPIO pin
                    if device.get("unit") == "°C" and device.get("gpio_pin"):
                        # Only process DS18B20 devices
                        if device.get("subtype") == "DS18B20":
                            temperature = self.read_ds18b20(device["gpio_pin"])  # Read temperature from DS18B20 sensor
                            if temperature is not None:
                                # Call update_sensor_data with temperature value
                                self.update_sensor_data(device["id"], temperature=temperature)  # Corrected call

            # Sleep for 90 seconds before checking again
            time.sleep(90)

        except Exception as e:
            logger.error(f"Error fetching devices or updating sensor data: {e}")
