import time
import signal
import sys
import schedule
import logging
import RPi.GPIO as GPIO

from config import logger
from supabase_client import SupabaseManager
from gpio_manager import GPIOManager
from system_monitor import SystemMonitor
from realtime_manager import RealtimeManager


class RaspberryPiController:
    def __init__(self):
        logger.info("Initializing Raspberry Pi Controller")

        self.supabase = SupabaseManager()
        self.gpio = GPIOManager()
        self.system = SystemMonitor()

        # Flag to control main loop
        self.running = False

        # Initialize realtime listener with callback
        self.realtime = RealtimeManager(self.handle_device_update)

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        logger.info("Controller initialized")

    def start(self):
        """Start the controller"""
        logger.info("Starting controller")

        # Connect to Supabase
        if not self.supabase.connect():
            logger.error("Failed to connect to Supabase, retrying in 10 seconds")
            time.sleep(10)
            return self.start()

        # Fetch and register devices
        self.register_devices()

        # Schedule periodic tasks
        schedule.every(5).minutes.do(self.register_devices)  # Re-sync devices periodically

        # Start realtime listener for immediate updates
        self.realtime.start()

        # Main loop
        self.running = True
        logger.info("Controller started")

        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()

    def register_devices(self):
        """Fetch devices from Supabase and register them with GPIO manager"""
        devices = self.supabase.get_devices()
        logger.info(f"Found {len(devices)} devices for this control unit")

        for device in devices:
            if not device.get('gpio_pin'):
                logger.warning(f"Device {device['id']} ({device['name']}) has no GPIO pin assigned, skipping")
                continue

            # Register with GPIO manager
            self.gpio.register_device(
                device['id'],
                device['gpio_pin'],
                device['type'],
                device.get('is_active', False),
                device.get('value')
            )

        return True

    def handle_device_update(self, event_type, device_data):
        """Handle realtime device updates"""
        device_id = device_data.get('id')

        if event_type == 'device_created':
            # New device added to this controller
            if device_data.get('gpio_pin'):
                self.gpio.register_device(
                    device_id,
                    device_data['gpio_pin'],
                    device_data['type'],
                    device_data.get('is_active', False),
                    device_data.get('value')
                )

        elif event_type == 'device_updated':
            # Device state updated in Supabase
            # Update local GPIO state
            self.gpio.update_device_state(
                device_id,
                device_data.get('is_active'),
                device_data.get('value')
            )

        elif event_type == 'device_deleted':
            # Device deleted, we might want to clean up
            # For now, just log it
            logger.info(f"Device {device_id} has been deleted")

    def signal_handler(self, sig, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {sig}, shutting down")
        self.running = False

    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources")

        # Stop realtime listener
        self.realtime.stop()

        # Set control unit to offline
        self.supabase.disconnect()

        # Clean up GPIO
        self.gpio.cleanup()

        logger.info("Shutdown complete")


if __name__ == "__main__":
    controller = RaspberryPiController()
    controller.start()