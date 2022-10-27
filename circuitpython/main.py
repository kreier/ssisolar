# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# SSIS adaptation: @emwdx and @kreier 2022-05-30 
# https://github.com/kreier/ssisolar/tree/main/circuitpython
# v0.4 2022-10-28

version = "v0.4 2022-10-28"

import time
import alarm
import microcontroller
from random import randint

import ssl
import socketpool
import wifi
import board
import gc
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT

## Set up analog in
from analogio import AnalogIn

input_voltage_1 = AnalogIn(board.IO7)   # the current over 0.5 Ohm as voltage
input_voltage_2 = AnalogIn(board.IO8)   # the solar voltage divided by 5.7

def get_voltage(pin):
    return (pin.value * 3.3) / 65536

print("SSISolar " + version)

### WiFi ###

# Add a secrets.py to your filesystem that has a dictionary called secrets
# with "ssid" and "password" keys with your WiFi credentials. DO NOT share
# that file or commit it into Git or other source control.
# pylint: disable=no-name-in-module,wrong-import-order
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Set your Adafruit IO Username and Key in secrets.py
# (visit io.adafruit.com if you need to create an account,
# or if you need your Adafruit IO key.)
aio_username = secrets["aio_username"]
aio_password = secrets["aio_password"]
not_connected = True
while (not_connected):
    try:
        print("Connecting to %s" % secrets["ssid"])
        wifi.radio.connect(secrets["ssid"], secrets["password"])
        print("Connected to %s!" % secrets["ssid"])
        not_connected = False
    except:
        print("connection error, retrying")

# Define callback functions which will be called when certain events happen.
# pylint: disable=unused-argument
def connected(client):
    # Connected function will be called when the client is connected to Adafruit IO.
    # This is a good place to subscribe to feed changes.  The client parameter
    # passed to this function is the Adafruit IO MQTT client so you can make
    # calls against it easily.
    print("Connected to Adafruit IO!")
    # Subscribe to changes on a feed named DemoFeed.
    #client.subscribe("DemoFeed")
    not_connected = False


def subscribe(client, userdata, topic, granted_qos):
    # This method is called when the client subscribes to a new feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))


def unsubscribe(client, userdata, topic, pid):
    # This method is called when the client unsubscribes from a feed.
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))


# pylint: disable=unused-argument
def disconnected(client):
    # Disconnected function will be called when the client disconnects.
    print("Disconnected from Adafruit IO!")
    not_connected = False


# pylint: disable=unused-argument
def message(client, feed_id, payload):
    # Message function will be called when a subscribed feed has a new value.
    # The feed_id parameter identifies the feed, and the payload parameter has
    # the new value.
    print("Feed {0} received new value: {1}".format(feed_id, payload))


# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)

# Initialize a new MQTT Client object
mqtt_client = MQTT.MQTT(
    broker   = "io.adafruit.com",
    username = aio_username,
    password = aio_password,
    socket_pool = pool,
    ssl_context = ssl.create_default_context(),
)

# Initialize an Adafruit IO MQTT Client
io = IO_MQTT(mqtt_client)

# Connect the callback methods defined above to Adafruit IO
io.on_connect = connected
io.on_disconnect = disconnected
io.on_subscribe = subscribe
io.on_unsubscribe = unsubscribe
io.on_message = message

# Connect to Adafruit IO
print("Connecting to Adafruit IO...")
io.connect()

# Below is an example of manually publishing a new  value to Adafruit IO.
last = 0
print("Publishing a new message every 60 seconds...")
while True:
    # Explicitly pump the message loop.

    # Send a new message every 31 seconds.
    if (time.monotonic() - last) >= 31:
        input_current = get_voltage(input_voltage_1) * 15 - 0.44 
        # the current over 0.5 Ohm as voltage offset correction: 
        # the measured solar voltage includes the voltage drop over the
        # 0.5 Ohm current resistor. But now we've taken this measurement and can subtract
        # it to get the correct value: input_voltage_1 is now the voltage over a 0.5 Ohm
        # resistor times 3, so we could subtract this value divided by 3 from the solar voltage
        # the voltage we measure is the solar voltage divided by 5.7 (47 kOhm and 10 kOhm series)
        # so we have to divide the input_value_1 by 3 and 5.7 before subtracting from
        # the submitted value for input_value_2

        input_voltage = get_voltage(input_voltage_2) - (input_current / ( 25))
        # the solar voltage divided by 5.7
        print("P: {0} V and {1} A. ".format(input_current,input_voltage), end='')
        print(gc.mem_free())
        if gc.mem_free() < 4000000:
            gc.collect()
        try:
            io.loop()
            io.publish("current", input_current)
            print("Submitted current ..",end="")
            time.sleep(2)
            io.publish("voltage", input_voltage)
            print("submitted voltage ..",end="")
            time.sleep(2)
            io.publish("memory", gc.mem_free())
            print("and free memory.")
            print("Now waiting 50 seconds to reset.")
            for loop in range(2):
                for i in range(25):
                    print(".", end='')
                    time.sleep(1)
                print("")
            # sometimes this does not work as expected. reset just in case    
            # microcontroller.reset()
            #al = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 60)
            #alarm.exit_and_deep_sleep_until_alarms(al)
            print("\ndeep sleep for 20 seconds")
            time.deep_sleep(20)
        except:
            while(not_connected):
                print("reconnecting")
                io.connect()
                time.sleep(2.0)
        last = time.monotonic()
