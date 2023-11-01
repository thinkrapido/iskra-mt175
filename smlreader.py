
# Python code to read values from Smart Meter via SML (smart message language) 
# created: Alexander Kabza, Mar 1, 2016
# last mod: Alexander Kabza, 2020-03-01
# modified by AF 2023-03-26 for writing to influxdb2
# For documentation and further information see http://www.kabza.de/MyHome/SmartMeter/SmartMeter.html
# 
# Start with nohup pipenv run python3 test.py &

import sys
import os
import serial
import time
import numpy as np

from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

if os.environ.get('INFLUX_TOKEN') is not None:
    token = os.environ.get('INFLUX_TOKEN') 
else:
    print ("You must set env INFLUX_TOKEN")
    exit()

if os.environ.get('INFLUX_ORG') is not None:
    org = os.environ.get('INFLUX_ORG') 
else:
    print ("You must set env INFLUX_ORG")
    exit()

if os.environ.get('INFLUX_BUCKET') is not None:
    bucket = os.environ.get('INFLUX_BUCKET') 
else:
    print ("You must set env INFLUX_BUCKET")
    exit()

if os.environ.get('INFLUX_HOST') is not None:
    influx_url=os.environ.get('INFLUX_HOST')
else:
    print ("You must set env INFLUX_BUCKET")
    exit()

if os.environ.get('SERIAL_PORT') is not None:
    serial_port=os.environ.get('SERIAL_PORT')
else:
    print ("You must set env SERIAL_PORT such as /dev/ttyS0")
    exit()

client = InfluxDBClient(url=influx_url , token=token)
write_api = client.write_api(write_options=SYNCHRONOUS)

port = serial.Serial(
    port=serial_port,
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)

start = '1b1b1b1b01010101'
end = '1b1b1b1b1a'
data = ''
a = np.empty(0, dtype=float)
now = datetime.now()
starttimestamp = (now.strftime("%Y-%m-%d ") + now.strftime("%H:%M:%S"))
prevminute = 321

while True:
    char = port.read()
    data = data + char.hex()
    pos = data.find(end)
    #print(data)
    #print(pos)
    if (pos != -1):
        for x in range(0, 3):       # read three more byte after end of SML message (checksum etc)
            char = port.read()
            data = data + char.hex()        
  
        now = datetime.now()
        timestamp = (now.strftime("%Y-%m-%d ") + now.strftime("%H:%M:%S"))
        result = timestamp
        #print(data)

        #ExtendedOutput(data)
    
        search = '77078181c78203ff0101010104'
        pos = data.find(search)
        if (pos != -1):
            pos = pos + len(search)
            value = data[pos:pos + 6]
            #print('Hersteller-ID:   ' + search + ': ' + value + ' = ' + bytes.fromhex(value).decode('utf-8'))  #value.fromhex())

        search = '77070100000009ff010101010b'
        pos = data.find(search)
        if (pos != -1):
            pos = pos + len(search)
            value = data[pos:pos + 20]
            #print('Server-ID:       ' + search + ': ' + value)

        energy = 0
        search = '77070100010800ff65'
        pos = data.find(search)
        #print("pos energy:" + str(pos))
        if (pos != -1):
            pos = pos + len(search) + 20  # skip 9 Bytes which may be different
            value = data[pos:pos + 16]
            try:
                energy = float(int(value, 16)) / 10000
            except:
                energy = 0.0   
            #print ('Total Bezug:     ' + search + ': ' + value + ' = ' + str(energy) + ' kWh')
        result = result + ";" + str(energy)
        
        power = 0
        search = '77070100100700ff0101621b520055'
        pos = data.find(search)
        if (pos != -1):
            pos = pos + len(search)
            value = data[pos:pos + 8]
            try:
                power = float(int(value, 16))
            except:
                power = 0.0
            #print('Leistung:        ' + search + ': ' + value + ' = ' + str(power) + ' W')
        result = result + ";" + str(power)

        a = np.append(a, power)
        
        powerL1 = 0   
        search = '070100240700ff0101621b520055'
        pos = data.find(search)
        if (pos != -1):
            pos = pos + len(search)
            value = data[pos:pos + 8]
            try:
                powerL1 = int(value, 16)
            except:
                powerL1 = 0.0
            #print('Leistung L1:        ' + search + ': ' + value + ' = ' + str(powerL1) + ' W')
        result = result + ";" + str(powerL1)

        a = np.append(a, powerL1)

        powerL2 = 0   
        search = '070100380700ff0101621b520055'
        pos = data.find(search)
        if (pos != -1):
            pos = pos + len(search)
            value = data[pos:pos + 8]
            try:
                powerL2 = int(value, 16)
            except:
                powerL2 = 0.0
            #print('Leistung L2:        ' + search + ': ' + value + ' = ' + str(powerL2) + ' W')
        result = result + ";" + str(powerL2)

        a = np.append(a, powerL2)

        powerL3 = 0   
        search = '0701004c0700ff0101621b520055'
        pos = data.find(search)
        if (pos != -1):
            pos = pos + len(search)
            value = data[pos:pos + 8]
            try:
                powerL3 = int(value, 16)
            except:
                powerL3 = 0.0
            #print('Leistung L3:        ' + search + ': ' + value + ' = ' + str(powerL3) + ' W')
        result = result + ";" + str(powerL3)

        a = np.append(a, powerL3)

        sequence = ["power,L=L power="+str(power),
            "power,L=L1 power="+str(powerL1),
            "power,L=L2 power="+str(powerL2), 
            "power,L=L3 power="+str(powerL3),
            "power,direction=in energy="+str(energy)]
        write_api.write(bucket, org, sequence)      
        data = ''