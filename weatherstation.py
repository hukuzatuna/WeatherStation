#!/usr/bin/python
##############################################################################
# weatherstation.py - Collect weather sensor data and upload them to
# Weather Underground.
#
# NOTE: Weather Underground has rolled their server certs and now there is
# an FQND vs. certificate name mismatch, meaning you can't update your PWS
# securely. This version doesn't use WU but instead pushes all data to an
# MQTT broker running on a Raspberry Pi 4. I'll write a module that reads
# reads the data from there and attempts to push to WU
#
# Author:      Phil Moyer (phil@moyer.ai)
# Date:        January 2020
#
# License: This program is released under the MIT license. Any
# redistribution must include this header.
##############################################################################

######################
# Import Libraries
######################

# Standard libraries modules

import time
import time
import string
import math
# import urllib2
# import urllib.parse
# import urllib.request
from w1thermsensor import W1ThermSensor
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

# Third-party modules

from Adafruit_BME280 import *
import Adafruit_ADS1x15

# Package/application modules

import PRMqueue


######################
# Globals
######################

Debug = True

client = mqtt.Client(protocol=mqtt.MQTTv311)
client.connect(host="cupcake", port=1883)

ds18b20 = W1ThermSensor()
# bme = BME280(t_mode=BME280_OSAMPLE_8, p_mode=BME280_OSAMPLE_8, h_mode=BME280_OSAMPLE_8)
bme = BME280()
adc = Adafruit_ADS1x15.ADS1115()

interval = 15  #How long we want to wait between loops (seconds)
windTick = 0   #Used to count the number of times the wind speed input is triggered
rainTick = 0   #Used to count the number of times the rain input is triggered

# Two minute wind data (windspeedmph_avg2m and winddir_avg2m)

tlen = (60/interval) * 2

twoMinSpeed = PRMqueue.PRMQueue(tlen)
twoMinDir = PRMqueue.PRMQueue(tlen)

tlen = (60/interval) * 10

tenMinGustSpeed = PRMqueue.PRMQueue(tlen)
tenMinGustDir = PRMqueue.PRMQueue(tlen)

tlen = (60/interval) * 60

longGustSpeed = PRMqueue.PRMQueue(tlen)
longGustDir = PRMqueue.PRMQueue(tlen)
hourlyRainData = PRMqueue.PRMQueue(tlen)

tlen = (60/interval) * 60 * 24

dailyRainData = PRMqueue.PRMQueue(tlen)

#Set GPIO pins to use BCM pin numbers
GPIO.setmode(GPIO.BCM)

#Set digital pin 17 to an input and enable the pullup 
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Set digital pin 23 to an input and enable the pullup 
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Event to detect wind (4 ticks per revolution)
GPIO.add_event_detect(17, GPIO.BOTH) 

def windtrig(self):
# def windtrig():
    global windTick
    windTick += 1

GPIO.add_event_callback(17, windtrig)

#Event to detect rainfall tick
GPIO.add_event_detect(23, GPIO.FALLING)
def raintrig(self):
# def raintrig():
    global rainTick
    rainTick += 1

GPIO.add_event_callback(23, raintrig)

# Weather Underground configuration
# WUserver = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"

fieldLabels = ["humidity",
               "tempf",
               "baromin",                   # Pressure
               "dewpoint",
               "winddir",
               "windspeedmph"
               "windgustmph",
               "windgustdir",
               "windspeedmph_avg2m",
               "winddir_avg2m",
               "windgustmph_10m",
               "windgustdir_10m",
               "rainin",
               "dailyrainin"];

fieldUnits = [ "percent",
               "degrees",
               "in Hg",
               "F",
               "degrees",
               "mph",
               "mph",
               "degrees",
               "mph",
               "degrees",
               "mph",
               "degrees",
               "in",
               "in"];


######################
# Classes and Methods
######################

class WeatherData2():
    def __init__(self):
        self.WXdata = {}
        self.WXdata["humidity"] = 0.0              # Relative Humidty, percent
        self.WXdata["tempf"] = 0.0                 # Temperature, degrees F
        self.WXdata["baromin"] = 0.0               # Barometric pressure, in Hg
        self.WXdata["dewptf"] = 0.0                # Dew Point, degrees F
        self.WXdata["winddir"] = 0.0               # Wind direction, degrees
        self.WXdata["windspeedmph"] = 0.0          # Wind speed, mph
        self.WXdata["windgustmph"] = 0.0           # Wind gust max, over time period, mph
        self.WXdata["windgustdir"] = 0.0           # Wind gust max direction, over time period, degrees
        self.WXdata["windspeedmph_avg2m"] = 0.0    # Wind speed, two minute average, mph
        self.WXdata["winddir_avg2m"] = 0.0         # Wind direction, two minute average, degrees
        self.WXdata["windgustmph_10m"] = 0.0       # Wind gust max, 10 minute period, mph
        self.WXdata["windgustdir_10m"] = 0.0       # Wind gust max direction, degrees
        self.WXdata["rainin"] = 0.0                # Current rainfall, inches/hour
        self.WXdata["dailyrainin"] = 0.0           # 24 hour rainfall, inches

    def printWXdata(self):
        print(self.WXdata)

    def prettyPrintData(self):
        for key in sorted(curWeatherData.WXdata):
            print("%s:\t%f" % (key, curWeatherData.WXdata[key]))
        print("\n")

    def fixPressure(self):
        # Returns mb instead of hpa.
        self.WXdata['baromin'] = float(self.WXdata['baromin']) / 100.0
        # x = (29.92 * 1034) / 1013.25 = 30.53 inches of mercury
        self.WXdata['baromin'] = ((29.92 * self.WXdata['baromin'])/1013.25)
        return(self.WXdata['baromin'])

    def sendToWU(self):                 # Send weather data to Weather Underground
        # https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?
        # ID=KCASANFR5&PASSWORD=XXXXXX&dateutc=2000-01-01+10%3A32%3A35&winddir=230&
        # windspeedmph=12&windgustmph=12&tempf=70&rainin=0&baromin=29.1&dewptf=68.2&
        # humidity=90&weather=&clouds=&softwaretype=vws%20versionxx&action=updateraw


        url = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"

        values = {'ID' : WUstation,
            'PASSWORD' : WUpass,
            'dateutc' : 'now',
        }
        for key in curWeatherData.WXdata:
            values[key] = repr(curWeatherData.WXdata[key])
            # outBuf = outBuf + "&" + key + "=" + repr(curWeatherData.WXdata[key])

        data = urllib.parse.urlencode(values)
        data = data.encode('ascii') # data should be bytes
        print(data)
        req = urllib.request.Request(url, data)
        with urllib.request.urlopen(req) as response:
            the_page = response.read()
        return

        # outBuf = WUserver + "?ID=" + WUstation + "&PASSWORD=" + WUpass
        # outBuf = outBuf + "&dateutc=now"
        # for key in curWeatherData.WXdata:
            # outBuf = outBuf + "&" + key + "=" + repr(curWeatherData.WXdata[key])
        # print(outBuf)
        # try:
            # result = urllib2.urlopen(outBuf)
        # except urllib2.URLError:
            # print("failed: URLError")
            # return
        # print(result.info())
        # resp = result.read()
        # print(resp)
        # result.close()
        # return

curWeatherData = WeatherData2()


######################
# Pre-Main Setup
######################

try:
    from secrets import secrets
except ImportError:
    print("Weather Underground secrets are kept in secrets.py, please add them there!")
    raise

# Get sensor location data
sensorLat = secrets["sensorLat"]
sensorLon = secrets["sensorLon"]
sensorMGRS = secrets["sensorMGRS"]
# Get URL connection data
Wuuser=secrets["WUuser"]
WUpass=secrets["WUpass"]
WUstation=secrets["WUstation"]

######################
# Functions
######################

def fixPressure(pascals):
    # Returns mb instead of hpa.
    baromin = float(pascals) / 100.0
    # x = (29.92 * 1034) / 1013.25 = 30.53 inches of mercury
    rv = ((29.92 * baromin)/1013.25)
    return(rv)


# Convert Celcius to Kelvin
def CtoK(degC):
    rv = float(degC + 273.15)
    return(rv)


# Convert Farenheit to Kelvin
def FtoK(degF):
    rv = float((degF + 459.67) * (5.0/9.0))
    return(rv)


# Convert Kelvin to Celcius
def KtoC(degK):
    rv = float(degK - 273.15)
    return(rv)


# Convert Kelvin to Farenheit
def KtoF(degK):
    rv = float(degK * (9.0/5.0) - 459.67)
    return(rv)

# Convert Celcius to Farenheit
def CtoF(degC):
    return float(degC * (9.0/5.0) + 32.0)

# Calculate the dew  point using the Clausius-Clapeyron equations:
# RH = 100% x (E/Es)
# E = E0 x exp[(L/Rv) x {(1/T0) - (1/Td)}]
# Es = E0 x exp[(L/Rv) x {(1/T0) - (1/T)}]
def calcDewPoint(tempF, relHum):
    tempK = FtoK(tempF)
    Es = 0.611 * math.exp(5423 * ((1.0/273.0) - (1.0/tempK)))
    # (relHum/100.0 * Es) = E0 * math.exp(5423 * (1.0/273.0) - (1.0/Td))
    # math.ln((relHum/00.0 * Es)/0.611) = 5423 * ((1.0/273.0) - (1.0/Td))
    # math.ln((relHum/100.0) * Es)/5423.0 = (1.0/273.0) - (1.0/Td)
    # (math.ln((relHum/100.0) * Es)/5423.0) - (1.0/273.0) = - (1.0/Td)
    Td = -1.0/((math.log1p((relHum/100.0) * Es)/5423.0) - (1.0/273.0))
    return(KtoF(Td))

# Take a fast and rough approximation of dew point:
# Td = T - ((100 - RH)/5.)
def DPcheat(degF, relHum):
    degC = KtoC(FtoK(degF))    # Too lazy to write the FtoC() functions
    Td = degC - ((100 - relHum)/5.0)
    return(Td)

def NOAAdewPoint(degC, rh, press_mb):
    Tcalc = ((7.5 * degC)/(237.3 + degC))
    es = 6.11 * math.pow(10, Tcalc)
    num = 237.3 * math.log((es * rh)/611.0)
    den = (7.5 * math.log(10)) - math.log((es * rh)/611.0)
    rv = (num/den)
    # rv is in Celcius, we need it in Farenheit
    return(CtoF(rv))

def CtoF(tempc):
    return(tempc * (8.0/5.0) + 32.0)

def KPHtoMPH(kph):
    rv = float(kph) * 0.62137119
    return(rv)

def MMtoIN(mm):
    rv = float(mm) * 0.03937008
    return(rv)

def getQMean(inQueue):
    # Returns mean of data elements in passed Queue object
    return inQueue.dataMean()

def getQMaxPair(inQOne, inQTwo):
    tIndex = inQOne.dataMaxIndex()
    maxData = inQOne.getItem(tIndex)
    maxDataCItem = inQTwo.getItem(tIndex)
    return (maxData, maxDataCItem)

def getQSum(inQueue):
    # Takes a Queue object as input, returns the sum of the data
    return inQueue.dataSum()


######################
# Main
######################

while True:

    time.sleep(interval)

    #Pull Temperature from DS18B20
    degrees = ds18b20.get_temperature()

    #Pull temperature from BME280
    case_temp = bme.read_temperature()

    #Pull pressure from BME280 Sensor & convert to kPa
    pressure_pa = bme.read_pressure()
    pressure = fixPressure(pressure_pa)

    #Pull humidity from BME280
    humidity = bme.read_humidity()

    #Calculate wind direction based on ADC reading
    val = adc.read_adc(0, gain=1) #Read ADC channel 0 with a gain setting of 1

    if 20000 <= val <= 20500:
        windDir = "N"
        windDeg = 0

    if 10000 <= val <= 10500:
        windDir = "NNE"
        windDeg = 22.5

    if 11500 <= val <= 12000:
        windDir = "NE"
        windDeg = 45

    if 2000 <= val <= 2250:
        windDir = "ENE"
        windDeg = 67.5

    if 2300 <= val <= 2500:
        windDir = "E"
        windDeg = 90

    if 1500 <= val <= 1950:
        windDir = "ESE"
        windDeg = 112.5

    if 4500 <= val <= 4900:
        windDir = "SE"
        windDeg = 135

    if 3000 <= val <= 3500:
        windDir = "SSE"
        windDeg = 157.5

    if 7000 <= val <= 7500:
        windDir = "S"
        windDeg = 180

    if 6000 <= val <= 6500:
        windDir = "SSW"
        windDeg = 202.5

    if 16000 <= val <= 16500:
        windDir = "SW"
        windDeg = 225

    if 15000 <= val <= 15500:
        windDir = "WSW"
        windDeg = 247.5

    if 24000 <= val <= 24500:
        windDir = "W"
        windDeg = 270

    if 21000 <= val <= 21500:
        windDir = "WNW"
        windDeg = 292.5

    if 22500 <= val <= 23000:
        windDir = "NW"
        windDeg = 315

    if 17500 <= val <= 18500:
        windDir = "NNW"
        windDeg = 337.5

    #Calculate average windspeed over the last 15 seconds
    windSpeed = (windTick * 1.2) / interval
    windTick = 0

    #Calculate accumulated rainfall over the last 15 seconds
    rainFall = rainTick * 0.2794
    rainTick = 0

    # PRM's clculations

    tempf = CtoF(degrees)
    dewPoint = NOAAdewPoint(degrees, humidity, pressure)
    windSpeed = KPHtoMPH(windSpeed)
    rainFall = MMtoIN(rainFall)

    # Maintain the data queues for Max and Average calculations
    
    twoMinSpeed.put(windSpeed)
    twoMinDir.put(windDeg)
    tenMinGustSpeed.put(windSpeed)
    tenMinGustDir.put(windDeg)
    longGustSpeed.put(windSpeed)
    longGustDir.put(windDeg)
    dailyRainData.put(rainFall)
    hourlyRainData.put(rainFall)

    # Toss the oldest item in the queue

    twoMinSpeed.get()
    twoMinDir.get()
    tenMinGustSpeed.get()
    tenMinGustDir.get()
    longGustSpeed.get()
    longGustDir.get()
    dailyRainData.get()
    hourlyRainData.get()

    # Figure out the averages (2 min) and max (10 min and 1 hr)

    t2MinAvgSpd = getQMean(twoMinSpeed)
    t2MinAvgDir = getQMean(twoMinDir)
    (t10MinMaxSpd,t10MinMaxDir) = getQMaxPair(tenMinGustSpeed, tenMinGustDir)
    (tlongGustSpd,tlongGustDir) = getQMaxPair(longGustSpeed, longGustDir)
    tDailyRain = getQSum(dailyRainData)
    thourlyRain = getQSum(hourlyRainData)

    # Print the results

    curWeatherData.prettyPrintData()

    # Update the data structures

    curWeatherData.WXdata["humidity"] = humidity
    curWeatherData.WXdata["tempf"] = tempf
    curWeatherData.WXdata["baromin"] = pressure
    curWeatherData.WXdata["dewptf"] = dewPoint
    curWeatherData.WXdata["winddir"] = windDeg
    curWeatherData.WXdata["windspeedmph"] = windSpeed
    curWeatherData.WXdata["rainin"] = thourlyRain
    curWeatherData.WXdata["windspeedmph_avg2m"] = t2MinAvgSpd
    curWeatherData.WXdata["winddir_avg2m"] = t2MinAvgDir
    curWeatherData.WXdata["windtustmph_10m"] = t10MinMaxSpd
    curWeatherData.WXdata["windgustdir_10m"] = t10MinMaxDir
    curWeatherData.WXdata["windgustmph"] = tlongGustSpd
    curWeatherData.WXdata["windgustdir"] = tlongGustDir
    curWeatherData.WXdata["dailyrainin"] = tDailyRain

    client.publish(topic="weather/humidity", payload=humidity)
    client.publish(topic="weather/tempf", payload=tempf)
    client.publish(topic="weather/pressure", payload=pressure)
    client.publish(topic="weather/dewPoint", payload=dewPoint)
    client.publish(topic="weather/windDeg", payload=windDeg)
    client.publish(topic="weather/windSpeed", payload=windSpeed)
    client.publish(topic="weather/hourlyRain", payload=thourlyRain)
    client.publish(topic="weather/2MinAvgSpd", payload=t2MinAvgSpd)
    client.publish(topic="weather/2MinAvgDir", payload=t2MinAvgDir)
    client.publish(topic="weather/10MinMaxSpd", payload=t10MinMaxSpd)
    client.publish(topic="weather/10MinMaxDir", payload=t10MinMaxDir)
    client.publish(topic="weather/longGustSpd", payload=tlongGustSpd)
    client.publish(topic="weather/longGustDir", payload=tlongGustDir)
    client.publish(topic="weather/DailyRain", payload=tDailyRain)

    # Send data to Weather Underground
    # Note: weather cam is handled by viking.

    # curWeatherData.sendToWU()

# Sample urllib code

# import urllib.parse
# import urllib.request

# url = 'http://www.someserver.com/cgi-bin/register.cgi'
# values = {'name' : 'Michael Foord',
#           'location' : 'Northampton',
#           'language' : 'Python' }

# data = urllib.parse.urlencode(values)
# data = data.encode('ascii') # data should be bytes
# req = urllib.request.Request(url, data)
# with urllib.request.urlopen(req) as response:
#    the_page = response.read()

