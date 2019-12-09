# WeatherStation
Read weather instruments and push data to Weather Underground

## Overview

To be written. (Sorry)

## Dependencies

### Hardware
- Adafruit [BME280 sensor breakout](https://www.adafruit.com/product/2652)
- Waterproof [DS18B20 temperature sensor](https://www.adafruit.com/product/381)
- SparkFun [Weather Instruments](https://www.sparkfun.com/products/8942)
- Adafruit [ADS1115 16-bit ADC](https://www.adafruit.com/product/1085)
- Raspberry Pi 3 B+ or newer
- (Optional) Raspberry Pi Camera
- (Optional) [2m Raspberry Pi Camera Cable](https://www.adafruit.com/product/2144)
- Mounting hardware appropriate for your installation

### Software

- Patched [Raspbian](https://downloads.raspberrypi.org/raspbian_full_latest)
- Python 3.7
- pip3
- Adafruit Blinka
- Adafruit ADS1x15 CircuitPython library
- Adafruit BME28 CircuitPython library
- urllib
- w1thermsensor
- RPi.GPIO
- Weather Underground account

## Setup

  pip3 install adafruit_GPIO
  pip3 install adafruit_blinka
  pip3 install adafruit_circuitpython_BME280
  pip3 install Adafruit_CircuitPython_ADS1x15

Setup to run wetherstation.py and re-starting it if it crashes for some reason.
Edit the secrets.py file like
  secrets = {
    'WUuser' : 'CHANGE TO YOUR WU USER ID',
    'WUpass' : 'CHANGE TO YOUR WU PASSWORD',
    'WUstation' : 'YOUR STATION ID',
    'sensorLat' : deicmal degrees latitude of the station,
    'sensorLon' : decimal degrees longitude of the station,
    'sensorMGRS' : ;
    'Military Grid Reference System coordinates (unused)',
    }

Watch the output to be sure the data collection is working and the authentication to Weather Underground is working, too.
