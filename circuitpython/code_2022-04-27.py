# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Adaptation for SSIS: @emwdx and @kreier 2022-04-27
# code.py for the METRO ESP32-S2 Express from Adafruit

import time
import gc
import rtc
from random import randint

import ssl
import socketpool
import wifi
import board
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT


## Set up analog in
from analogio import AnalogIn

input_voltage_1 = AnalogIn(board.A0)   # the current over 0.5 Ohm as voltage
input_voltage_2 = AnalogIn(board.A5)   # the solar voltage divided by 5.7

def get_voltage(pin):
    return (pin.value * 3.3) / 65536

class RTC(object):
    @property
    def datetime(self):
        return time.struct_time((2022, 4, 11, 08, 0, 0, 0, 0, 0))

r = rtc.RTC()
def now_print():
    print("{:02}/{:02}/{:04} {:02}:{:02}:{:02}".format(
        r.datetime.tm_mday,
        r.datetime.tm_mon,
        r.datetime.tm_year,
        r.datetime.tm_hour,
        r.datetime.tm_min,
        r.datetime.tm_sec),
    )

now_print()
rtc.set_time_source(r)
now_print()

### WiFi ###

# Add a secrets.py to your filesystem that has a dictionary called secrets with "ssid" and
# "password" keys with your WiFi credentials. DO NOT share that file or commit it into Git or other
# source control.
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
aio_key = secrets["aio_key"]
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
    broker="io.adafruit.com",
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
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
print("Publishing a new message every 20 seconds...")
while True:
    # Explicitly pump the message loop.

    # Send a new message every 20 seconds.
    if (time.monotonic() - last) >= 20:
        input_value_1 = get_voltage(input_voltage_1) * 15 - 0.2 # the current over 0.5 Ohm as voltage
        # offset correction: the measured solar voltage includes the voltage drop over the
        # 0.5 Ohm current resistor. But now we've taken this measurement and can subtract
        # it to get the correct value: input_voltage_1 is now the voltage over a 0.5 Ohm
        # resistor times 3, so we could subtract this value divided by 3 from the solar voltage
        # the voltage we measure is the solar voltage divided by 5.7 (47 kOhm and 10 kOhm series)
        # so we have to divide the input_value_1 by 3 and 5.7 before subtracting from
        # the submitted value for input_value_2

        input_value_2 = get_voltage(input_voltage_2) - (input_value_1 / ( 25 ))
        # the solar voltage divided by 5.7
        print("Send {0} A and {1} V to AIO. ".format(input_value_1,input_value_2), end='')
        print(gc.mem_free(), "Bytes free. ", end='')
        now_print()
        gc.collect()
        try:
            print("loop",end='')
            io.loop()
            print(". solar-stuff-1", end='')
            io.publish("solar-stuff-1", input_value_1)
            print("=current, solar-stuff-2", end='')
            time.sleep(2.0)
            io.publish("solar-stuff-2", input_value_2)
            print("=voltage.")
        except:
            while(not_connected):
                print("reconnecting")
                io.connect()
                time.sleep(2.0)
        last = time.monotonic()
