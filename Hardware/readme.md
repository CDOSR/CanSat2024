# Hardware

CAD sources for the custom PCBs designed for CanSat 2024.

## Contents

- `PCB Designs/` — Eagle `.sch` (schematic) and `.brd` (board layout) files
  for the four custom boards:
  - `Comm_board_2024_L76` — communications board with Quectel L76 GNSS
  - `Comm_board_2024_M8N` — communications board with u-blox NEO-M8N GNSS
  - `Power_board_2024` — power distribution and battery management
  - `Sensor_board_2024` — sensor aggregation (IMU, environmental, etc.)

## Component datasheets

Datasheets for the third-party components used on these boards live under
[`Documentation/Hardware/Data Sheets/`](../Documentation/Hardware/Data%20Sheets/)
— kept separate so this tree stays focused on our own CAD sources rather
than vendor reference material.
