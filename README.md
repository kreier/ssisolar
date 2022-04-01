# ssisolar
Documentation of Photovoltaic Potential at SSIS

## Project description

We want to explore the potential and challenges of photovoltaic systems by creating and maintaining an example system. For further investigation we want to collect as much data as possible.



## History

### April 1st, 2022

The internet connection is rather unstable or to far away for our ESP32S2. Restarting circuitpython with the REPL or reset starts the transmission, but the rendered graphs connects the last two values with a straight line, which might be confusing. Se the jump in  the voltage measurement (times 5.7) at the beginning of April first:

![2022-04-01 Voltage](docs/2022-04-01_voltage.jpg)

Another update involves the current measurement. With a peak current of 1.5 Ampere the reading would only be 0.75 Volt. Thats small compared to the peak raw voltage measurement of 2 Volt after the 1:5.7 voltage divider. So I multiply the measurement by 3 to give it a comparable range during the day for the combined plot.

![2022-04-01 Current](docs/2022-04-01_current.jpg)


### March 30th, 2022

Our first measurement with ESP32S2 and Adafruit IO, having voltage and current sensor running parallel. Combined the values of the last 24 hours are in [the dashboard](https://io.adafruit.com/emwdx/dashboards/solar-dash) but we have [voltage](https://io.adafruit.com/emwdx/feeds/solar-stuff-2) and [current](https://io.adafruit.com/emwdx/feeds/solar-stuff-1) individually too. First day (with lost connections and incomplete ssl handshakes) looks like this:

![2022-03-30](docs/2022-03-30.jpg)

With Logger Pro from Vernier we collect current and voltage in parallel. To overcome the sensor limitations we attached the voltage probe (6 Volt max) to a 1:3 30kOhm voltage divider. And we added a 0.05 Ohm resistor parallel to the internal resistor of 0.1 Ohm of the 0.6 Amperemeter.

![2022-03-29](docs/2022-03-29.jpg)

The picture above shows the data collection on our iMac from sunset __March 27th__ to sunset __March 29th__. The two syncronous positive periods in <span style="color:blue">🔵voltage</span> and <span style="color:red">🔴current</span> are sunlight daytime March 28th and 29th. Two features stick out: 

- __Noise:__ With the addition of the Metro ESP32S2, connected via USB to the iMac for power, programming and REPL we also grounded the solar installation itself. The differential voltage and current meters from the Vernier LabQuest setup collected a lot of noise from the 30 long cable to the solar panel, that collected a lot of static noise over the distance. The setup was added in the afternoon of March 28th, as seen in the clear lower noise of the red current collection and the drop in measured blue voltage for the solar panel. It now matches the voltage of the battery.

- __Rain at 9:00 PM on March 27th:__ This Monday night a thunderstorm with heavy rain crossed over Saigon. This can be seen in the peak of __red current__ noise during the first night measurement. The voltage stays unaffected at zero.

The installation itself collects data since Friday, 2022-03-18.
