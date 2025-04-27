# Import required modules
from machine import Pin, TouchPad, PWM
import time
from neopixel import NeoPixel
import network
import socket

# Global variables
threshold = 80         # Touch threshold to trigger start/stop
timing = False         # Stopwatch state
start_time = 0         # Time when touch starts
elapsed = 0            # Time difference between start and stop
touch_pin = TouchPad(Pin(32))   # Setup touch sensor on Pin 32
led = Pin(2, Pin.OUT)          # Setup led on Pin 2

# HTML content for the web server (shows elapsed time and status)
html = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Time interval</title>
    <style>
        /* Basic CSS styling for better visual appearance */
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; margin: 0; padding: 20px; text-align: center; color: #333; }
        .container { background-color: white; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); padding: 20px; max-width: 600px; margin: 0 auto; }
        h1 { color: #2c3e50; font-size: 2.5em; margin-bottom: 10px; }
        .timer { font-size: 3em; font-weight: bold; color: #e74c3c; margin: 20px 0; }
        .status { font-size: 1.5em; padding: 10px; border-radius: 5px; margin: 20px 0; display: inline-block; }
        .running { background-color: #2ecc71; color: white; }
        .stopped { background-color: #e74c3c; color: white; }
    </style>
    <script>
        // JavaScript to fetch and update elapsed time every 100ms
        function updateTime() {
            fetch(window.location.href + 'data')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('elapsed').innerText = data.elapsed;
                    let statusElem = document.getElementById('status');
                    statusElem.innerText = data.status;
                    statusElem.className = 'status ' + (data.status === 'Running' ? 'running' : 'stopped');
                })
                .catch(error => console.error('Error fetching data:', error));
        }
        setInterval(updateTime, 100);  // Repeat update every 100ms
    </script>
</head>
<body>
    <div class="container">
        <h1>Time interval</h1>
        <div class="timer"><span id="elapsed">%d</span> ms</div>
        <div id="status" class="status %s">%s</div>
    </div>
</body>
</html>
"""

# JSON format to return elapsed time and status to AJAX
json_response = """{"elapsed": %d, "status": "%s"}"""

# led to indicate system start
led.value(1)
time.sleep(1)

# Function to connect ESP32 to WiFi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to network...")
        wlan.connect(ssid, password)
        for i in range(20):
            if wlan.isconnected():
                break
            print("Waiting for connection...")
            time.sleep(1)
    if wlan.isconnected():
        print("Network config:", wlan.ifconfig())
        return True
    return False


def handle_connection(s):
    try:
        conn, addr = s.accept()
        try:
            request = conn.recv(1024).decode()

            # Determine current timing state
            status = "Running" if timing else "Stopped"
            status_class = "running" if timing else "stopped"

            if request.find("/data") > 0:
                response = json_response % (elapsed, status)
                conn.send("HTTP/1.1 200 OK\n")
                conn.send("Content-Type: application/json\n")
                conn.send("Access-Control-Allow-Origin: *\n")
                conn.send("Connection: close\n\n")
                conn.send(response)
            else:
                response = html % (elapsed, status_class, status)
                conn.send("HTTP/1.1 200 OK\n")
                conn.send("Content-Type: text/html\n")
                conn.send("Connection: close\n\n")
                conn.send(response)
        except Exception as e:
            print("Error handling connection:", e)
        finally:
            conn.close()
    except OSError:
        pass
    except Exception as e:
        print("Unexpected error in connection handler:", e)

# Main function
def main():
    global timing, start_time, elapsed, threshold

    # WiFi credentials
    WIFI_SSID = "pleaseconnect"
    WIFI_PASSWORD = "veryeasy"

    # Connect to WiFi network
    if not connect_wifi(WIFI_SSID, WIFI_PASSWORD):
        print("WiFi connection failed")
        return
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 80))
        s.listen(5)
        s.setblocking(False)
        print("Web server started")
    except OSError as e:
        print("Socket error:", e)
        return

    # Short led to indicate ready
    print("Waiting for touch input...")

    while True:
        touch_val = touch_pin.read()  # Read touch sensor value

        # If not currently timing and touch is detected, start timer
        if not timing and touch_val < threshold:
            start_time = time.ticks_ms()
            timing = True #stopwatch status updated by this variable
            print("Stopwatch started")
            led.value(1)  # led ON

        # If timing and touch is released, stop timer
        elif timing and touch_val > threshold:
            elapsed = time.ticks_diff(time.ticks_ms(), start_time)
            timing = False
            print("Stopwatch stopped. Elapsed time: {} ms".format(elapsed))
            led.value(0)  # led OFF
        handle_connection(s)
        time.sleep_ms(8)

if __name__ == "__main__":
    main()
