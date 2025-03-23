import RPi.GPIO as GPIO

class GPIOHandler:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

    def setup_pin(self, device):
        gpio_pin = device.get('gpio_pin')
        if gpio_pin is None or not isinstance(gpio_pin, int):
            print(f"Invalid GPIO pin for device {device['id']}: {gpio_pin}")
            return
        GPIO.setup(gpio_pin, GPIO.OUT if device['type'] in ['Spínač', 'Termostat'] else GPIO.IN)

    def update_pin_state(self, device):
        gpio_pin = device.get('gpio_pin')
        if gpio_pin is None or not isinstance(gpio_pin, int):
            print(f"Invalid GPIO pin for device {device['id']}: {gpio_pin}")
            return
        value = GPIO.HIGH if device['value'] else GPIO.LOW
        GPIO.output(gpio_pin, value)

    def read_sensor(self, device):
        gpio_pin = device.get('gpio_pin')
        if gpio_pin is None or not isinstance(gpio_pin, int):
            print(f"Invalid GPIO pin for sensor {device['id']}: {gpio_pin}")
            return None
        return GPIO.input(gpio_pin)
