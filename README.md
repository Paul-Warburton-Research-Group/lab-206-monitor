## Dilution Fridge Monitoring Software

This set of programs is used to monitor dilution fridge vitals remotely. There is software available for both Oxford Instruments and Bluefors systems.

### Setup

Links to the following files should be created in the modules directory of your python installation:
 * `client/triton_data_client.py`
 * `client/xld_data_client.py`
 * `arduino/arduino_client.py`

### Server-Client

A server that runs on the PC supplied by the dil. fridge manufacturer parses log files periodically and serves the available data on the ethernet port. A number of PCs can then connect to the server via a switch. The client software can then be used on the host PCs to query sensor measurement data.

Client Files:
 * `client/triton_data_client.py`: A module that is imported in python measurement scripts (Triton version).
 * `client/xld_data_client.py`: A module that is imported in python measurement scripts (XLD version).

Server Files:
 * `server/parse_triton_log.py`: Used by the server to parse the Triton logfiles.
 * `server/parse_xld_log.py`: Used by the server to parse the Bluefors XLD logfiles. Should work the same for other models.
 * `server/triton_data_server.py`: The server script. Run this ensuring that the address and port are reachable by a host. Firewall rules may need to be created.

### Arduino

An Arduino is used to monitor building services to the dilution fridge. Currently, the compressed air pressure/temperature, and the mass of the liquid nitrogen trap are measured periodically.

The Arduino firmware is the file `arduino/M32JM-firmware-v1.ino`, which configures the serial connection and performs reading of the sensors every second. Python scripts can communicate with the Arduino using the `arduino_client.py` file which defines the `ArduinoClient` class. The `read()` function is used to update the current measurements (blocks until the Arduino performs the next measurement), which can be accessed using other functions.

The pressure sensor is connected to a T-junction on the CDA inlet. The current model used is [a 100psi sensor](https://uk.rs-online.com/web/p/pressure-sensors/2074701/). This sensor has an integrated temperature sensor which is also used but currently doesn't tell us much apart from maybe the state of the air-conditioning in the lab.

The mass of the LN2 trap is measured using a hacked load cell from a cheap commercial scale. The Arduino is fitted with the HX711 load cell SparkFun board, which is operated using the Arduino library created by Bogdan Necula. The scale was precalibrated using a known mass.

### Monitor

A monitor GUI is available that displays live measurements from the dilution fridge and the Arduino sensors. It is configured using the `config.cfg` file and executed with `python live_plotter.py` on Windows. It should be possible to create a shortcut from the desktop and/or in the start menu. The file `Triton Monitor.cmd` was an attempt towards this.