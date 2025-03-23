import RPi.GPIO as GPIO


class GPIOHandler:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.initialized_pins = {}

    def setup_pin(self, device):
        pin = int(device['gpio_pin'])
        if pin in self.initialized_pins:
            return
        GPIO.setup(pin, GPIO.OUT if device['type'] in ['Spínač', 'Termostat'] else GPIO.IN)
        if device['type'] in ['Spínač', 'Termostat']:
            GPIO.output(pin, GPIO.HIGH if device['is_active'] else GPIO.LOW)
        self.initialized_pins[pin] = device['id']

    def update_pin_state(self, device):
        if not device.get('gpio_pin'):
            return
        pin = int(device['gpio_pin'])
        GPIO.output(pin, GPIO.HIGH if device['is_active'] else GPIO.LOW)

    def read_sensor(self, device):
        if not device.get('gpio_pin'):
            return None
        return GPIO.input(int(device['gpio_pin']))