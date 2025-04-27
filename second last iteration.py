#import libraries
from machine import Pin, TouchPad
import time
from neopixel import NeoPixel


threshold = 300  # Touch threshold value
timing = False  # Stores stopwatch status
start_time = 0  # Start time
elapsed = 0  # Time interval when not gripping the cylinder
pixel_pos = 0  # Stores led position to reverse light off from that position

# Setup touch sensor and output pins
touch_pin = TouchPad(Pin(33))

#motor pins
in1 = Pin(13, Pin.OUT)
in2 = Pin(12, Pin.OUT)

buzz = Pin(2, Pin.OUT)  #buzzer pin

# Setup NeoPixel LED strip
n_lights = 59  # Number of NeoPixels
datapin = Pin(4, Pin.OUT)  # Data pin for NeoPixels
np = NeoPixel(datapin, n_lights)  # Initialize NeoPixels

print("Waiting for touch input...")

# ----------------------------
# Main loop
# ----------------------------
while True:
    touch_val = touch_pin.read()  # Read touch sensor value

    # --- Start timing if touch detected ---
    if not timing and touch_val < threshold:
        start_time = time.ticks_ms()  # Record start time
        timing = True  # Set timing active
        in1.value(1)  #rotation start
        in2.value(0)
        buzz.value(1)  # Turn buzzer ON
        print("Stopwatch started")

    # --- Stop timing if touch released ---
    elif timing and touch_val > threshold:
        elapsed = time.ticks_diff(time.ticks_ms(), start_time)  # Calculate elapsed time
        timing = False  # Set timing inactive
        in1.value(0)  # rotation stopped
        in2.value(0)  #
        buzz.value(0)  # Turn buzzer OFF
        print("Stopwatch stopped. Elapsed time: {} ms".format(elapsed))

    # --- LED animation while timing ---
    if timing:
        elapsed = time.ticks_diff(time.ticks_ms(), start_time)  # Update elapsed time
        now = elapsed  # (Optional duplicate, could clean)
        for i in range(n_lights): #140 so that pixel position doesn't loop to lesser value
            touch_val = touch_pin.read()  # Continuously read touch to break in between
            if touch_val < threshold:
                    np[n_lights - 1 - i] = (0, 100, 0)
                    np.write()
                    time.sleep_ms(80)  # Delay for animation effect
            else:
                pixel_pos = i
                break

    # --- LED clearing when timing stops ---
    if not timing:
        buzz.value(0)  # Make sure buzzer is OFF
        for i in range(n_lights - pixel_pos, n_lights):  # Clear from last lit LED forward
            touch_val = touch_pin.read()  # Monitor touch
            if touch_val > threshold:  # Only clear if touch is not active
                np[i] = (0, 0, 0)
                np.write()  # Update LEDs
                time.sleep_ms(30)  # Small delay for smooth clearing
