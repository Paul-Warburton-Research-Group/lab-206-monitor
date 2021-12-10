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

An Arduino is used to monitor building services to the dilution fridge. Currently, the compressed air pressure/temperature, and the temperature of the liquid nitrogen trap are measured periodically.

### Monitor

A monitor GUI is available that displays live measurements from the dilution fridge and the Arduino sensors. It is configured using the `config.cfg` file and executed with `python live_plotter.py` on Windows. It should be possible to create a shortcut from the desktop and/or in the start menu. The file `Triton Monitor.cmd` was an attempt towards this.