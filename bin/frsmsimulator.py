#!/usr/bin/env python
"""
Fronius Smart Meter Simulator (MODBUS) Version 1.0
--------------------------------------------------------------------------

This script simulates a Fronius Smart Meter for providing necessary 
information to inverters (e.g. SYMO, SYMO HYBRID) for statistics. 
Necessary information is provied via MQTT and translated to MODBUS RTU

"""
# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from pymodbus.version import version
from pymodbus.server.asynchronous import StartSerialServer, StopServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
from threading import Lock
import struct
import time
import json
import getopt
import sys
import socket
import signal
import os

# --------------------------------------------------------------------------- #
# import the twisted libraries we need
# --------------------------------------------------------------------------- #
from twisted.internet.task import LoopingCall

# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# handle start arguments
# --------------------------------------------------------------------------- #
inputs = None
outputs = None
loglevel=logging.ERROR
logfile=""
logfileArg = ""
lbhomedir = ""
configfile = ""
opts, args = getopt.getopt(sys.argv[1:], 'f:l:c:h:', ['logfile=', 'loglevel=', 'configfile=', 'lbhomedir='])
for opt, arg in opts:
    if opt in ('-f', '--logfile'):
        logfile=arg
        logfileArg = arg
    elif opt in ('-l', '--loglevel'):
        loglevel=map_loglevel(arg)
    elif opt in ('-c', '--configfile'):
        configfile=arg
    elif opt in ('-h', '--lbhomedir'):
        lbhomedir=arg

# --------------------------------------------------------------------------- #
# get configuration from mqtt broker and store config in mqttconf variable
# --------------------------------------------------------------------------- #
mqttconf = None;

MQTT_DEFAULT_PORT = "1883"

#try:
with open(lbhomedir + '/data/system/plugindatabase.json') as json_plugindatabase_file:
        plugindatabase = json.load(json_plugindatabase_file)
        mqttconfigdir = plugindatabase['plugins']['07a6053111afa90479675dbcd29d54b5']['directories']['lbpconfigdir']

        mqttPluginconfig = None
        with open(mqttconfigdir + '/mqtt.json') as json_mqttconfig_file:
            mqttPluginconfig = json.load(json_mqttconfig_file)

        mqttcred = None
        with open(mqttconfigdir + '/cred.json') as json_mqttcred_file:
            mqttcred = json.load(json_mqttcred_file)

        mqttuser = mqttcred['Credentials']['brokeruser']
        mqttpass = mqttcred['Credentials']['brokerpass']
        mqttaddressArray = mqttPluginconfig['Main']['brokeraddress'].split(":")
        mqttPort = MQTT_DEFAULT_PORT
        if len(mqttaddressArray) > 1:
            mqttPort = int(mqttaddressArray[1])

        mqttconf = {
            'username':mqttuser,
            'password':mqttpass,
            'address': mqttaddressArray[0],
            'port': mqttPort
        }


#    _LOGGER.debug("MQTT config" + str(mqttconf))
#except Exception as e:
#    _LOGGER.exception(str(e))

# If no mqtt config found leave the script with log entry
#if mqttconf is None:
#    _LOGGER.critical("No MQTT config found. Daemon stop working")
#    sys.exit(-1)

# --------------------------------------------------------------------------- #
# Reading custom parameters out of paramter file
# --------------------------------------------------------------------------- #
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(lbhomedir + '/config/plugins/frosim_folder/config.cfg')

MQTT_TOPIC_CONSUMPTION  = config.get('CONFIGURATION','TOPIC_CONSUMPTION')
MQTT_TOPIC_TOTAL_IMPORT = config.get('CONFIGURATION','TOPIC_TOTAL_IMPORT')
MQTT_TOPIC_TOTAL_EXPORT = config.get('CONFIGURATION','TOPIC_TOTAL_EXPORT')
corrfactor = config.get('CONFIGURATION','CORRFACTOR')
i_corrfactor = int(corrfactor)
serialport = config.get('CONFIGURATION','SERIAL_PORT')

print MQTT_TOPIC_TOTAL_EXPORT
print MQTT_TOPIC_TOTAL_IMPORT
print MQTT_TOPIC_CONSUMPTION
print corrfactor
print serialport

# --------------------------------------------------------------------------- #
# configure MQTT service
# --------------------------------------------------------------------------- #
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe

lock = Lock()

leistung = "0"
einspeisung = "0"
netzbezug = "0"

ti_int1 = "0"
ti_int2 = "0"
exp_int1 = "0"
exp_int2 = "0"
ep_int1 = "0"
ep_int2 = "0"

mqttc = mqtt.Client()
mqttc.username_pw_set(mqttconf['username'], mqttconf['password'])
mqttc.connect(mqttconf['address'], mqttconf['port'], 60)

mqttc.subscribe(MQTT_TOPIC_CONSUMPTION)
mqttc.subscribe(MQTT_TOPIC_TOTAL_IMPORT)
mqttc.subscribe(MQTT_TOPIC_TOTAL_EXPORT)

mqttc.loop_start()

def terminateProcess(signalNumber, frame):
    print('(SIGTERM) terminating the process')
    StopServer()

def on_message(client, userdata, message):
    global leistung
    global einspeisung
    global netzbezug

    print("Received message '" + str(message.payload) + "' on topic '"
        + message.topic + "' with QoS " + str(message.qos))

    lock.acquire()

    if message.topic == MQTT_TOPIC_CONSUMPTION:
       leistung = message.payload
    elif message.topic == MQTT_TOPIC_TOTAL_IMPORT:
        netzbezug = message.payload
    elif message.topic == MQTT_TOPIC_TOTAL_EXPORT:
        einspeisung = message.payload

    lock.release()

mqttc.on_message = on_message


#def terminateProcess(signalNumber, frame):
#   print('(SIGTERM) terminating the process')
#    StopServer()

# --------------------------------------------------------------------------- #
# define your callback process
# --------------------------------------------------------------------------- #


def updating_writer(a):
    """ A worker process that runs every so often and
    updates live values of the context. It should be noted
    that there is a race condition for the update.

    :param arguments: The input arguments to the call
    """

    global ep_int1
    global ep_int2
    global exp_int1
    global exp_int2
    global ti_int1
    global ti_int2

    lock.acquire()
    #Considering correction factor 
    print("Korrigierte Werte")
    float_netzbezug = float(netzbezug)
    netzbezug_corr = float_netzbezug*i_corrfactor
    print netzbezug_corr

    float_einspeisung = float(einspeisung)
    einspeisung_corr = float_einspeisung*i_corrfactor
    print einspeisung_corr

    #Converting current power consumption out of MQTT payload to Modbus register

    electrical_power_float = float(leistung) #extract value out of payload
    print electrical_power_float
    electrical_power_hex = struct.pack('>f', electrical_power_float).encode('hex') #convert float value to float32 and further to hex
    electrical_power_hex_part1 = str(electrical_power_hex)[0:4] #extract first register part (hex)
    electrical_power_hex_part2 = str(electrical_power_hex)[4:8] #extract seconds register part (hex)
    ep_int1 = int(electrical_power_hex_part1, 16) #convert hex to integer because pymodbus converts back to hex itself
    ep_int2 = int(electrical_power_hex_part2, 16) #convert hex to integer because pymodbus converts back to hex itself

    #Converting total import value of smart meter out of MQTT payload into Modbus register

    total_import_float = int(netzbezug_corr)
    print total_import_float
    total_import_hex = struct.pack('>f', total_import_float).encode("hex")
    total_import_hex_part1 = str(total_import_hex)[0:4]
    total_import_hex_part2 = str(total_import_hex)[4:8]
    ti_int1  = int(total_import_hex_part1, 16)
    ti_int2  = int(total_import_hex_part2, 16)

    #Converting total export value of smart meter out of MQTT payload into Modbus register

    total_export_float = int(einspeisung_corr)
    print total_export_float
    total_export_hex = struct.pack('>f', total_export_float).encode("hex")
    total_export_hex_part1 = str(total_export_hex)[0:4]
    total_export_hex_part2 = str(total_export_hex)[4:8]
    exp_int1 = int(total_export_hex_part1, 16)
    exp_int2 = int(total_export_hex_part2, 16)

    log.debug("updating the context")
    context = a[0]
    register = 3
    slave_id = 0x01
    address = 0x9C87
    values = [0, 0,               #Ampere - AC Total Current Value [A]
              0, 0,               #Ampere - AC Current Value L1 [A]
              0, 0,               #Ampere - AC Current Value L2 [A]
              0, 0,               #Ampere - AC Current Value L3 [A]
              0, 0,               #Voltage - Average Phase to Neutral [V]
              0, 0,               #Voltage - Phase L1 to Neutral [V]
              0, 0,               #Voltage - Phase L2 to Neutral [V]
              0, 0,               #Voltage - Phase L3 to Neutral [V]
              0, 0,               #Voltage - Average Phase to Phase [V]
              0, 0,               #Voltage - Phase L1 to L2 [V]
              0, 0,               #Voltage - Phase L2 to L3 [V]
              0, 0,               #Voltage - Phase L1 to L3 [V]
              0, 0,               #AC Frequency [Hz]
              ep_int1, 0,         #AC Power value (Total) [W] ==> Second hex word not needed
              0, 0,               #AC Power Value L1 [W]
              0, 0,               #AC Power Value L2 [W]
              0, 0,               #AC Power Value L3 [W]
              0, 0,               #AC Apparent Power [VA]
              0, 0,               #AC Apparent Power L1 [VA]
              0, 0,               #AC Apparent Power L2 [VA]
              0, 0,               #AC Apparent Power L3 [VA]
              0, 0,               #AC Reactive Power [VAr]
              0, 0,               #AC Reactive Power L1 [VAr]
              0, 0,               #AC Reactive Power L2 [VAr]
              0, 0,               #AC Reactive Power L3 [VAr]
              0, 0,	          #AC power factor total [cosphi]
              0, 0,               #AC power factor L1 [cosphi]
              0, 0,               #AC power factor L2 [cosphi]
              0, 0,               #AC power factor L3 [cosphi]
              exp_int1, exp_int2, #Total Watt Hours Exportet [Wh]
              0, 0,               #Watt Hours Exported L1 [Wh]
              0, 0,               #Watt Hours Exported L2 [Wh]
              0, 0,               #Watt Hours Exported L3 [Wh]
              ti_int1, ti_int2,   #Total Watt Hours Imported [Wh]
              0, 0,               #Watt Hours Imported L1 [Wh]
              0, 0,               #Watt Hours Imported L2 [Wh]
              0, 0,               #Watt Hours Imported L3 [Wh]
              0, 0,               #Total VA hours Exported [VA]
              0, 0,               #VA hours Exported L1 [VA]
              0, 0,               #VA hours Exported L2 [VA]
              0, 0,               #VA hours Exported L3 [VA]
              0, 0,               #Total VAr hours imported [VAr]
              0, 0,               #VA hours imported L1 [VAr]
              0, 0,               #VA hours imported L2 [VAr]
              0, 0                #VA hours imported L3 [VAr]
]

    context[slave_id].setValues(register, address, values)

    lock.release()

    signal.signal(signal.SIGTERM,terminateProcess)

def run_updating_server():
    # ----------------------------------------------------------------------- # 
    # initialize your data store
    # ----------------------------------------------------------------------- # 
    lock.acquire()
 
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [15]*100),
        co=ModbusSequentialDataBlock(0, [15]*100),
        hr=ModbusSparseDataBlock({

        40001:  [21365, 28243], 
        40003:  [1],
        40004:  [65],
        40005:  [70,114,111,110,105,117,115,0,0,0,0,0,0,0,0,0,         #Manufacturer "Fronius"
		83,109,97,114,116,32,77,101,116,101,114,32,54,51,65,0, #Device Model "Smart Meter 63A"
		0,0,0,0,0,0,0,0,                                       #Options N/A
                0,0,0,0,0,0,0,0,                                       #Software Version  N/A
		48,48,48,48,48,48,48,49,0,0,0,0,0,0,0,0,               #Serial Number: 00000001 (49,54,50,50,48,49,49,56
                240],                                                  #Modbus TCP Address: 240
        40070: [213],
        40071: [124], 
        40072: [0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0],

                40196: [65535, 0],

}),

	ir=ModbusSequentialDataBlock(0, [15]*100))
    context = ModbusServerContext(slaves=store, single=True)

    lock.release()

    # ----------------------------------------------------------------------- # 
    # run the server you want
    # ----------------------------------------------------------------------- # 
    time = 5  # 5 seconds delay
    loop = LoopingCall(f=updating_writer, a=(context,))
    loop.start(time, now=True) # initially delay by time

    StartSerialServer(context, port=serialport, baudrate=9600, stopbits=1, bytesize=8, framer=ModbusRtuFramer)


values_ready = False

while not values_ready:
      print("Warten auf Daten von MQTT Broker")
      time.sleep(1)
      lock.acquire()
      if netzbezug  != '0' and einspeisung != '0':
         print("Daten vorhanden. Starte Modbus Server")
         values_ready = True
      lock.release()
run_updating_server()
