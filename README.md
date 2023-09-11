# LDS-006 Lidar reverse engineering
## Introduction
This repository contains MVP Python application for LDS-006 and
motor control program for Arduino-compatible board 

## How to use
### Motor control
#### Warning! Section is deprecated! It's enough to send just "startlds$" string to UART and lidar will start spinning by itself!

For now, it is not yet known how to activate the motor via UART.
To solve this, I have made a simple Arduino sketch that is listening to the same UART line as the lidar itself.
It is looking for the specific parcel:  
| Header (1 byte) | Motor PWM Value (1 byte) | Ending (1 byte) |
| --------------- | ------------------------ | --------------- |
| ! (0x21)        | 0-255  (0x00 - 0xFF)     | ! (0x21)        |

It uses Arduino's internal PWM to control the external MOSFET transistor.
You can use any transistor you have in stocks. In my case, it's Chinese fake IRF 520 (a bit overkill for this, I guess). 
Don't forget about the pull-up resistor on MOSFET (I am using 4.7k, but 10k will be better).
More info about MOSFET wiring can be found in the STM32 demo repository [Link 3].   
Wiring scheme:
| Arduino       | Connection                |
| ------------- | ------------------------- |
| RX            | RX  (Grey on 4pin Lidar)  |
| VCC (5V)      | 5V (Red on 4pin Lidar)    |
| GND           | GND (Black on 4pin Lidar) |
| D10 (PWM out) | MOSFET Gate               |

The code is available in the `sketch` folder. It's pretty easy to understand and well commented, so feel free to read and modify it.

### Lidar data handling
The only known command for this lidar is 0x24 (USD character). 
Lidar is replying with 0x21 byte (exclamation mark) and starting to send data over UART when it's rotated.
Full protocol description can be found in the STM32 demo repository [Link 3].  
I had made a simple python class with all main reading functionality and the endless reading loop.
Just install all required libraries, correct the COM port number and run `python3 read.py`.

## Motor speed tuning
This lidar is highly sensitive to motor rotation speed. You should implement a good tuning algorithm. 
In my case lidar sending correct data (and not sending Speed error) on level 74+-1 of PWM on start and
71+-1 after about 15 minutes of work. I suggest you to run `for speed in range(64, 128)` loop to find your perfect working speed.
Make sure to let lidar work for a couple of seconds on each speed level because motor speed
is not changing instantly. This is a nice place to implement the library with PID speed contorol.

## Links
1. [Custom firmware project](https://github.com/0x416c6578/lds-006-firmware) by [0x416c6578](https://github.com/0x416c6578)
2. [Research](https://0x416c6578.github.io/lds-006/overview.html) by [0x416c6578](https://github.com/0x416c6578)
3. [STM32F4 + LCD demo for LDS-006](https://github.com/Aluminum-z/Laser-Radar-LDS-006-Drive-Test) by [Aluminum-z](https://github.com/Aluminum-z) 
