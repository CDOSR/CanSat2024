from machine import Pin, PWM
import time

# Initialize the PWM pin for the buzzer
buzzer = PWM(Pin(21))
# Initialize the enable pin for the buzzer
buzz_en = Pin(21, Pin.OUT)

def activate_buzzer(frequency=1000):
    """Activate the buzzer with the given frequency."""
    buzz_en.value(1)  # Enable the buzzer power/activation line
    buzzer.freq(frequency)  # Set the frequency of the sound
    buzzer.duty_u16(32768)  # Set duty cycle to 50% for audible sound

def deactivate_buzzer():
    """Deactivate the buzzer."""
    buzzer.duty_u16(0)  # Stop the PWM signal
    buzz_en.value(0)  # Disable the buzzer power/activation line

def test_buzzer(duration=1):
    """Test the buzzer by turning it on and off."""
    print("Buzzer ON")
    activate_buzzer()
    time.sleep(duration)  # Buzzer stays on for the specified duration
    print("Buzzer OFF")
    deactivate_buzzer()
    time.sleep(duration)  # Buzzer stays off for the specified duration

# Run the test function
test_buzzer()
