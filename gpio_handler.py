import RPi.GPIO as GPIO

class GPIOHandler:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

    def setup_pin(self, device):
        GPIO.setup(device['gpio_pin'], GPIO.OUT if device['type'] in ['Spínač', 'Termostat'] else GPIO.IN)

    def update_pin_state(self, device):
        GPIO.output(device['gpio_pin'], GPIO.HIGH if device['value'] else GPIO.LOW)

    def read_sensor(self, device):
        return GPIO.input(device['gpio_pin'])
