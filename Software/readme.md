# Software Directory

This directory contains all the software-related files for the CanSat2024 project.

## Contents
- `Main Can/`: Source code for the CanSat's onboard firmware.
- `Base Station/`: Software for the ground control station.

## Firmware
The `Main Can/` directory contains the source code that runs on the CanSat's microcontroller. This code is responsible for sensor data collection, communication, and control operations.

### Building the Firmware
To build the firmware, navigate to the `firmware/` directory and use the provided Makefile:
```sh
cd `Main Can`
make
