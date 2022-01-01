#!/usr/bin/env python
"""
Pymodbus Server With Updating Thread
--------------------------------------------------------------------------

This is an example of having a background thread updating the
context while the server is operating. This can also be done with
a python thread::

    from threading import Thread

    thread = Thread(target=updating_writer, args=(context,))
    thread.start()
"""
# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from pymodbus.version import version
from pymodbus.server.asynchronous import StartSerialServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer

import struct

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
# configure MQTT service
# --------------------------------------------------------------------------- #
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("AMIS/#")

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


# --------------------------------------------------------------------------- #
# define your callback process
# --------------------------------------------------------------------------- #


def updating_writer(a):
    """ A worker process that runs every so often and
    updates live values of the context. It should be noted
    that there is a race condition for the update.

    :param arguments: The input arguments to the call
    """
    msg = subscribe.simple("AMIS/Leistung", hostname="localhost",
    port=1883, auth={'username':"XXXXXXXXXX",'password':"XXXXXXXXXXXXX"})
    print("%s %s" % (msg.topic, msg.payload))

    electrical_power_float = float(msg.payload) #extract value out of payload
    electrical_power_hex = struct.pack('>f', electrical_power_float).encode('hex') #convert float value to float32 and furhter to hex
    print electrical_power_hex
    hex_part1 = str(electrical_power_hex)[0:4]
    hex_part2 = str(electrical_power_hex)[4:8]
    print hex_part1
    print hex_part2
    dec_1 = int(hex_part1, 16)
    dec_2 = int(hex_part2, 16)
    print dec_1
    print dec_2

    log.debug("updating the context")
    context = a[0]
    register = 3
    slave_id = 0x01
    address = 0x9C87
    values = [16448, 0, #Ampere - AC Total Current Value [A]
              16448, 0, #Ampere - AC Current Value L1 [A]
              16448, 0, #Ampere - AC Current Value L2 [A]
              16448, 0, #Ampere - AC Current Value L3 [A]
              17254, 0, #Voltage - Average Phase to Neutral [V]
              17254, 0, #Voltage - Phase L1 to Neutral [V]
              17254, 0, #Voltage - Phase L2 to Neutral [V]
              17254, 0, #Voltage - Phase L3 to Neutral [V]
              17254, 0, #Voltage - Average Phase to Phase [V]
              17254, 0, #Voltage - Phase L1 to L2 [V]
              17254, 0, #Voltage - Phase L2 to L3 [V]
              17254, 0, #Voltage - Phase L1 to L3 [V]
              16968, 0, #AC Frequency [Hz]
              dec_1, 0, #AC Power value (Total) [W]
              17402, 0, #AC Power Value L1 [W]
              17402, 0, #AC Power Value L2 [W]
              17402, 0, #AC Power Value L3 [W]
              0,0,      #AC Apparent Power [VA]
              0,0,      #AC Apparent Power L1 [VA]
              0,0,      #AC Apparent Power L2 [VA]
              0,0,      #AC Apparent Power L3 [VA]
              0,0,      #AC Reactive Power [VAr]
              0,0,      #AC Reactive Power L1 [VAr]
              0,0,      #AC Reactive Power L2 [VAr]
              0,0,      #AC Reactive Power L3 [VAr]
              0,0,
              0,0,
              0,0, 
              0,0, 
              0,0,
              0,0,
              0,0,
              0,0,
              0,0, 
              0,0,
              0,0,
              0,0,
              6,0,
              0,0,
              0,0,
              0,0,
              0,0,
              0,0,
              0,0,
              0,0,
              0,0,
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0,   #NaN (Not supported) 32704 = 7FC0 = NaN
              32704,0    #NaN (Not supported) 32704 = 7FC0 = NaN
]
    log.debug("new values: " + str(dec_1) + str(dec_2))
    context[slave_id].setValues(register, address, values)

def run_updating_server():
    # ----------------------------------------------------------------------- # 
    # initialize your data store
    # ----------------------------------------------------------------------- # 
    
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [15]*100),
        co=ModbusSequentialDataBlock(0, [15]*100),
        hr=ModbusSparseDataBlock({
        
        #0:      [0],
        00001:   [0],
        00002:   [2300],
        00012:   [240],
        #769:    [0],
        #1707:   [0],
        40001:  [21365, 28243], 
        40003:  [1],
        40004:  [65],
        40005:  [70,114,111,110,105,117,0,0,0,0,
                0,0,0,0,0,0,83,109,97,114,
                116,32,77,101,116,101,114,32,54,51,
                65,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,49,54,
                50,50,48,49,49,56,0,0,0,0,
                0,0,0,0,

                0,240], 
        
        #40010: [0,0,0,0,0,0,0,0,0,0],

        40070: [213],
        40071: [124], 
        40072: [0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,17530,0,0,0,
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
         #      50001: [0,0]

}),

	ir=ModbusSequentialDataBlock(0, [15]*100))
    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- # 
    # run the server you want
    # ----------------------------------------------------------------------- # 
    time = 5  # 5 seconds delay
    loop = LoopingCall(f=updating_writer, a=(context,))
    loop.start(time, now=False) # initially delay by time
    StartSerialServer(context, port='/dev/ttyUSB1', baudrate=9600, stopbits=1, bytesize=8, framer=ModbusRtuFramer)

if __name__ == "__main__":
    run_updating_server()
