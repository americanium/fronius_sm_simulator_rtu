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
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer

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

client = mqtt.Client()

client.connect("localhost", 1883, 60)
client.username_pw_set("xxx", password="xxx")

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("AMIS/#")

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

client.on_connect = on_connect
client.on_message = on_message


# --------------------------------------------------------------------------- #
# define your callback process
# --------------------------------------------------------------------------- #


def updating_writer(a):
    """ A worker process that runs every so often and
    updates live values of the context. It should be noted
    that there is a race condition for the update.

    :param arguments: The input arguments to the call
    """
    log.debug("updating the context")
    context = a[0]
    register = 3
    slave_id = 0x01
    address = 0x9C40
    values = [1200, 1201]
    log.debug("new values: " + str(values))
    context[slave_id].setValues(register, address, values)

def run_updating_server():
    # ----------------------------------------------------------------------- # 
    # initialize your data store
    # ----------------------------------------------------------------------- # 
    
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [15]*100),
        co=ModbusSequentialDataBlock(0, [15]*100),
        hr=ModbusSequentialDataBlock(40001, [15]*2),
        ir=ModbusSequentialDataBlock(0, [15]*100))
    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- # 
    # run the server you want
    # ----------------------------------------------------------------------- # 
    time = 5  # 5 seconds delay
    loop = LoopingCall(f=updating_writer, a=(context,))
    loop.start(time, now=False) # initially delay by time
    #StartTcpServer(context, identity=identity, address=("localhost", 5020))
    StartSerialServer(context, port='/dev/ttyUSB1', baudrate=9600, stopbits=1, bytesize=8, framer=ModbusRtuFramer)

if __name__ == "__main__":
    run_updating_server()
