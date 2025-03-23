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
        logger.info("GPIO Manager initialized")

    def register_device(self, device_id, gpio_pin, device_type, initial_state=False, initial_value=None):
        """Register a device with its GPIO pin"""
        if not gpio_pin:
            logger.warning(f"Device {device_id} has no GPIO pin assigned, skipping")
            return False

        try:
            gpio_pin = int(gpio_pin)

            # Setup pin based on device type
            if device_type.lower() in ["switch", "relay", "light"]:
                GPIO.setup(gpio_pin, GPIO.OUT)
                # Set initial state
                GPIO.output(gpio_pin, GPIO.HIGH if initial_state else GPIO.LOW)
                self.devices[device_id] = (gpio_pin, initial_state, device_type, None)
                logger.info(
                    f"Registered output device {device_id} to GPIO {gpio_pin} with initial state {initial_state}")

            elif device_type.lower() in ["sensor", "temperature", "humidity", "thermostat"]:
                # For sensors, we would need to implement specific reading logic
                # For now, we'll just register them
                self.devices[device_id] = (gpio_pin, None, device_type, initial_value)
                logger.info(f"Registered sensor device {device_id} to GPIO {gpio_pin}")

            return True

        except ValueError:
            logger.error(f"Invalid GPIO pin number for device {device_id}: {gpio_pin}")
            return False
        except Exception as e:
            logger.error(f"Error registering device {device_id} to GPIO {gpio_pin}: {e}")
            return False

    def update_device_state(self, device_id, state=None, value=None):
        """Update a device's GPIO state"""
        if device_id not in self.devices:
            logger.warning(f"Device {device_id} not registered, cannot update state")
            return False

        gpio_pin, current_state, device_type, current_value = self.devices[device_id]

        try:
            # Update state for output devices
            if device_type.lower() in ["switch", "relay", "light"] and state is not None:
                GPIO.output(gpio_pin, GPIO.HIGH if state else GPIO.LOW)
                self.devices[device_id] = (gpio_pin, state, device_type, current_value)
                logger.info(f"Updated device {device_id} on GPIO {gpio_pin} to state {'ON' if state else 'OFF'}")

            # Update value for value-based devices (like thermostats)
            if value is not None:
                # For real implementation, you would need to handle PWM or other protocols
                # Here we just store the value
                self.devices[device_id] = (gpio_pin, current_state, device_type, value)
                logger.info(f"Updated device {device_id} on GPIO {gpio_pin} to value {value}")

            return True

        except Exception as e:
            logger.error(f"Error updating device {device_id} state: {e}")
            return False

    def read_sensor(self, device_id):
        """Read sensor value from GPIO"""
        if device_id not in self.devices:
            logger.warning(f"Device {device_id} not registered, cannot read sensor")
            return None

        gpio_pin, current_state, device_type, current_value = self.devices[device_id]

        # In a real implementation, you would have specific sensor reading code here
        # For example, reading from DHT22, DS18B20, etc.
        # This is just a simulation

        if device_type.lower() == "temperature":
            # Simulate temperature reading (replace with actual sensor code)
            simulated_value = 20 + (time.time() % 10)
            logger.debug(f"Read temperature sensor {device_id}: {simulated_value}°C")
            return simulated_value

        elif device_type.lower() == "humidity":
            # Simulate humidity reading (replace with actual sensor code)
            simulated_value = 40 + (time.time() % 20)
            logger.debug(f"Read humidity sensor {device_id}: {simulated_value}%")
            return simulated_value

        return current_value

    def cleanup(self):
        """Clean up GPIO"""
        GPIO.cleanup()
        logger.info("GPIO cleanup completed")