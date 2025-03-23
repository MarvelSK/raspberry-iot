import RPi.GPIO as GPIO
import logging
from config import logger
import time


class GPIOManager:
    def __init__(self):
        # Set GPIO mode (BCM)
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Dictionary to store GPIO configuration for devices
        # Key: device_id, Value: (gpio_pin, current_state)
        self.devices = {}

        # Dictionary to map device types in different languages to standard types
        self.device_type_mapping = {
            # English
            "switch": "switch",
            "light": "switch",
            "relay": "switch",
            "sensor": "sensor",
            "temperature": "temperature",
            "humidity": "humidity",
            "thermostat": "thermostat",
            # Slovak/Czech
            "spínač": "switch",
            "svetlo": "switch",
            "relé": "switch",
            "senzor": "sensor",
            "teplota": "temperature",
            "vlhkosť": "humidity",
            "termostat": "thermostat",
        }

        logger.info("GPIO Manager initialized")

    def get_standard_device_type(self, device_type):
        """Convert device type to standard type regardless of language"""
        if not device_type:
            return "unknown"

        lowered_type = device_type.lower()
        return self.device_type_mapping.get(lowered_type, "unknown")

    def register_device(self, device_id, gpio_pin, device_type, initial_state=False, initial_value=None):
        """Register a device with its GPIO pin"""
        if not gpio_pin:
            logger.warning(f"Device {device_id} has no GPIO pin assigned, skipping")
            return False

        try:
            gpio_pin = int(gpio_pin)

            # Standardize the device type
            standard_type = self.get_standard_device_type(device_type)

            if standard_type == "unknown":
                logger.error(f"Unknown device type '{device_type}' for device {device_id}")
                return False

            # Setup pin based on device type
            if standard_type in ["switch"]:
                GPIO.setup(gpio_pin, GPIO.OUT)
                # Set initial state
                GPIO.output(gpio_pin, GPIO.HIGH if initial_state else GPIO.LOW)
                self.devices[device_id] = (gpio_pin, initial_state, standard_type, None)
                logger.info(
                    f"Registered output device {device_id} to GPIO {gpio_pin} with initial state {initial_state}")

            elif standard_type in ["sensor", "temperature", "humidity", "thermostat"]:
                # For sensors, we would need to implement specific reading logic
                # For now, we'll just register them
                self.devices[device_id] = (gpio_pin, None, standard_type, initial_value)
                logger.info(f"Registered sensor device {device_id} to GPIO {gpio_pin}")

            return True

        except ValueError:
            logger.error(f"Invalid GPIO pin number for device {device_id}: {gpio_pin}")
            return False
        except Exception as e:
            logger.error(f"Error registering device {device_id} to GPIO {gpio_pin}: {e}")
            return False

    def update_device_state(self, device_id, state=None, value=None):
        """Update a device's GPIO state or value

        Args:
            device_id: Unique identifier for the device
            state: ON/OFF state for output devices
            value: Value for sensors/thermostats
        """
        if device_id not in self.devices:
            logger.warning(f"Device {device_id} not registered, cannot update state")
            return False

        gpio_pin, current_state, device_type, current_value = self.devices[device_id]

        try:
            if device_type.lower() in ["switch", "relay", "light"] and state is not None:
                GPIO.output(gpio_pin, GPIO.HIGH if state else GPIO.LOW)
                self.devices[device_id] = (gpio_pin, state, device_type, current_value)
                logger.info(f"Updated device {device_id} on GPIO {gpio_pin} to {'ON' if state else 'OFF'}")

            if value is not None:
                self.devices[device_id] = (gpio_pin, current_state, device_type, value)
                logger.info(f"Updated device {device_id} on GPIO {gpio_pin} to value {value}")

            return True

        except Exception as e:
            logger.error(f"Error updating device {device_id}: {e}")
            return False

    def read_sensor(self, device_id):
        """Read value from a sensor device

        Args:
            device_id: Unique identifier for the device

        Returns:
            Simulated sensor value or current value stored
        """
        if device_id not in self.devices:
            logger.warning(f"Device {device_id} not registered, cannot read sensor")
            return None

        gpio_pin, _, device_type, current_value = self.devices[device_id]

        try:
            if device_type.lower() == "temperature":
                simulated_value = 20 + (time.time() % 10)
                logger.debug(f"Temperature sensor {device_id}: {simulated_value:.1f}°C")
                return simulated_value

            elif device_type.lower() == "humidity":
                simulated_value = 40 + (time.time() % 20)
                logger.debug(f"Humidity sensor {device_id}: {simulated_value:.1f}%")
                return simulated_value

            return current_value

        except Exception as e:
            logger.error(f"Error reading sensor {device_id}: {e}")
            return None

    def cleanup(self):
        """Clean up GPIO resources"""
        GPIO.cleanup()
        logger.info("GPIO cleanup completed")
