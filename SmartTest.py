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
from threading import Lock
import struct
import time

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

lock = Lock()

leistung = "0"
einspeisung = "0"
netzbezug = "0"

mqttc = mqtt.Client()
mqttc.username_pw_set("loxberry", "nsQMdsC1Ok47v6Ok")
mqttc.connect("localhost")

mqttc.subscribe("AMIS/Leistung")
mqttc.subscribe("AMIS/Netzbezug_total")
mqttc.subscribe("AMIS/Netzeinspeisung_total")

def on_message(client, userdata, message):
    global leistung
    global einspeisung
    global netzbezug
    print("Received message '" + str(message.payload) + "' on topic '"
        + message.topic + "' with QoS " + str(message.qos))
    lock.acquire()
    if message.topic == "AMIS/Leistung":
       leistung = message.payload
    elif message.topic == "AMIS/Netzbezug_total":
        netzbezug = message.payload
    elif message.topic == "AMIS/Netzeinspeisung_total":
        einspeisung = message.payload
    lock.release()

mqttc.on_message = on_message

# --------------------------------------------------------------------------- #
# define your callback process
# --------------------------------------------------------------------------- #


def updating_writer(a):
    """ A worker process that runs every so often and
    updates live values of the context. It should be noted
    that there is a race condition for the update.

    :param arguments: The input arguments to the call
    """
    mqttc.loop_start()

    #Converting current power consumption out of MQTT payload to Modbus register
    lock.acquire()
    electrical_power_float = float(leistung) #extract value out of payload
    print electrical_power_float
    electrical_power_hex = struct.pack('>f', electrical_power_float).encode('hex') #convert float value to float32 and further to hex
    electrical_power_hex_part1 = str(electrical_power_hex)[0:4] #extract first register part (hex)
    electrical_power_hex_part2 = str(electrical_power_hex)[4:8] #extract seconds register part (hex)
    ep_int1 = int(electrical_power_hex_part1, 16) #convert hex to integer because pymodbus converts back to hex itself
    ep_int2 = int(electrical_power_hex_part2, 16) #convert hex to integer because pymodbus converts back to hex itself

    #Converting total import value of smart meter out of MQTT payload into Modbus register

    total_import_float = int(netzbezug)
    print total_import_float
    total_import_hex = struct.pack('>f', total_import_float).encode("hex")
    total_import_hex_part1 = str(total_import_hex)[0:4]
    total_import_hex_part2 = str(total_import_hex)[4:8]
    ti_int1  = int(total_import_hex_part1, 16)
    ti_int2  = int(total_import_hex_part2, 16)

    #Converting total export value of smart meter out of MQTT payload into Modbus register

    total_export_float = int(einspeisung)
    print total_export_float
    total_export_hex = struct.pack('>f', total_export_float).encode("hex")
    total_export_hex_part1 = str(total_export_hex)[0:4]
    total_export_hex_part2 = str(total_export_hex)[4:8]
    exp_int1 = int(total_export_hex_part1, 16)
    exp_int2 = int(total_export_hex_part2, 16)

    lock.release()

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
              exp_int1, exp_int2, #Total Watt Hours Exportet [Wh] ==> 11968Wh == JSON: EnergyReal_WAC_Minus_Absolute
              0, 0,               #Watt Hours Exported L1 [Wh] ==> 4000 ==> JSON: EnergyReal_WAC_Phase_1_Produced
              0, 0,               #Watt Hours Exported L2 [Wh] ==> 4000 ==> JSON: EnergyReal_WAC_Phase_2_Produced
              0, 0,               #Watt Hours Exported L3 [Wh] ==> 4000 ==> JSON: EnergyReal_WAC_Phase_3_Produced
              ti_int1, ti_int2,   #Total Watt Hours Imported [Wh]  1500Wh JSON: EnergyReal_WAC_Plus_Absolute
              0, 0,               #Watt Hours Imported L1 [Wh] 10000 ==> JSON: EnergyReal_WAC_Phase_1_Consumed
              0, 0,               #Watt Hours Imported L2 [Wh] 5000 ==> JSON: EnergyReal_WAC_Phase_2_Consumed
              0, 0,               #Watt Hours Imported L3 [Wh] 5000 ==> JSON: EnergyReal_WAC_Phase_3_Consumed
              0, 0,               #Total VA hours Exported [VA]
              0, 0,               #VA hours Exported L1 [VA]
              0, 0,               #VA hours Exported L2 [VA]
              0, 0,               #VA hours Exported L3 [VA]
              0, 0,               #Total VAr hours imported [VAr]
              0, 0,               #VA hours imported L1 [VAr]
              0, 0,               #VA hours imported L2 [VAr]
              0, 0                #VA hours imported L3 [VAr]
]
    #log.debug("new values: " + str(dec_1) + str(dec_2))
    context[slave_id].setValues(register, address, values)

def run_updating_server():
    # ----------------------------------------------------------------------- # 
    # initialize your data store
    # ----------------------------------------------------------------------- # 
    
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [15]*100),
        co=ModbusSequentialDataBlock(0, [15]*100),
        hr=ModbusSparseDataBlock({
        
        #00001:   [0],
        #00002:   [2300],
        #00012:   [240],
        40001:  [21365, 28243], 
        40003:  [1],
        40004:  [65],
        40005:  [70,114,111,110,105,117,115,0,0,0,
                0,0,0,0,0,0,83,109,97,114,
                116,32,77,101,116,101,114,32,54,51,
                65,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,49,54,
                50,50,48,49,49,56,0,0,0,0,
                0,0,0,0,

                0,240],
        40069: [240], 
        40010: [0,0,0,0,0,0,0,0,0,0],
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

    # ----------------------------------------------------------------------- # 
    # run the server you want
    # ----------------------------------------------------------------------- # 
    time = 5  # 5 seconds delay
    loop = LoopingCall(f=updating_writer, a=(context,))
    loop.start(time, now=False) # initially delay by time
    StartSerialServer(context, port='/dev/ttyUSB1', baudrate=9600, stopbits=1, bytesize=8, framer=ModbusRtuFramer)

values_ready = False

while not values_ready:
      print("warten")
      print(netzbezug)
      time.sleep(1)
      lock.acquire()
      if netzbezug  != '0' and einspeisung != '0':
         print("Datenda")
         values_ready = True
      lock.release()
print("starten")
print(netzbezug)
run_updating_server()
