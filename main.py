#!/usr/bin/env python
#IMPORTANT!!! - You must use this script as superuser

import os
import sys
import logging
import binascii
import pygatt
from io import BytesIO
import msgpack 
import json
import uuid 

#--You must choose an obtion between public and random
ADDRESS_TYPE = pygatt.BLEAddressType.public
#ADDRESS_TYPE = pygatt.BLEAddressType.random

def terminate(*args, **kwargs):
    adapter.stop()
    exit(1)

def dict_print(d, message):
    opt =-1
    print(20 * "-" + message + 20 * "-"+"\n")
    while opt<0 or opt>=len(d):
        print(''.join(["\t {0} - {1} \n".format(str(k), str(v[0])) for k, v in d.items()]))
        print(20 * "-" + len(message)*"-" + 20 * "-"+"\n")
        choice = raw_input("-SELECT OPTION: [0-" + str(len(d) - 1) + "]: ")
        opt = check_option(choice, min = 0, max = len(d)-1)
    return opt

def conn_auto():
    with open('config.json') as json_data_file:
        data = json.load(json_data_file)

        for k, v in data.items():
            address = v["address"].decode("utf-8")
            service_uuid = uuid.UUID(v["service_uuid"].decode("utf-8"))
            connect(address, service_uuid=service_uuid)

def conn_Manual():
    devices = adapter.scan(run_as_root = True, timeout = 3)
    select_device_opt(devices)

def read(device, uuid):
    try:
        print("-Read UUID %s: " % (uuid))
        response = device.char_read(uuid)
        print("\n\t-Value: %s\n" % (response))
        print("\n\t--Response %s") % msgpack.unpackb(response, raw=False)

    except:
        print("-ERROR: Couldn't read the characteristic of UUID %s", uuid)
        
def write(device, uuid):
    n = raw_input("Hoy many attributes you want to write?: ")
    message = []

    #for i in range(int(n)):
    #    message.append(raw_input("Key: "))
    #    message.append(int(raw_input("Value: ")))
    message.append("OPT")
    message.append(int(raw_input("Option: ")))
    pack = msgpack.packb(message, strict_types = True)
    device.char_write(uuid, bytearray(pack))


#--Connection mode options
CONN_OPT = dict({ 0:("AUTOMATIC CONNECTION", conn_auto), 1: ("MANUAL CONNECTION", conn_Manual), 2:("EXIT", terminate) })

#--Menu options
SELECT_DEVICE      = 0
SELECT_SERVICE     = 1
SELECT_OPTION      = 2
SELECT_CONN_MODE   = 3

#--Methods in service
OPERATION_OPT = dict({ 0:("CHAR_READ", read), 1:("CHAR_WRITE", write), 2:("EXIT", terminate) })

logging.basicConfig()
#logging.getLogger('pygatt').setLevel(logging.INFO)
logging.setLevel(logging.INFO)
log = logging.getLogger(__name__)

def check_option(opt, min = 0, max = 100):
    try:
        return int(opt) if min <= int(opt) and int(opt) <= max else -1
    except:
        print("ERROR you must introduce a valid option: 0-" + str(max) + "]")
        return

def select_device_opt(devices):
    d = dict((i, ({"Device":devices[i]["address"], "Name":devices[i]["name"]}, connect)) for i in range(len(devices)))
    d[len(d)]=("EXIT", None, terminate)
    opt = dict_print(d, "SELECT DEVICE")
    return d.get(opt)[1](d.get(opt)[0]["Device"])
     
def subscribe_service_opt(device, service_uuid=None):
   
    if service_uuid != None:
        device.subscribe(service_uuid, callback = handle_data)
        return service_uuid
    else:
        services = device.discover_characteristics().keys()
        s = dict((i, (services[i], device.subscribe)) for i in range(len(services)))
        s[len(s)]=("EXIT", terminate)
        opt = dict_print(s, "SERVICE")
        service_uuid = s.get(opt)[0]
        s.get(opt)[1](service_uuid, callback = handle_data)
        return service_uuid


def handle_data(handle, value):
    """
    handle -- integer, characteristic read handle the data was received on
    value -- bytearray, the data returned in the notification
    """
    log.('Received notification on handle=0x%x, value=0x%s',
                 handle, binascii.hexlify(value))

def interactions(device=None, service_uuid=None):
    while True:
        opt = dict_print(OPERATION_OPT, "SERVICE OPTIONS")
        print(OPERATION_OPT.get(opt)[1](device, service_uuid))

def connect(address, service_uuid=None):
    try:
        print("Connecting to", address)
        device = adapter.connect(address, address_type = ADDRESS_TYPE)

        while True:
            service_uuid = subscribe_service_opt(device, service_uuid=service_uuid)     
            if service_uuid!=None:
                print("Susccessful!")
                break
            
        interactions(device=device, service_uuid=service_uuid)
    except pygatt.exceptions.NotConnectedError:
        print("Failed to connect to %s" % address)

if __name__ == '__main__':
    adapter = pygatt.GATTToolBackend(hci_device = "hci0")
    adapter.start()
    for k, v in CONN_OPT.items():
        print("\t" + str(k) + " "+ v[0])
    choice = raw_input("-SELECT CONNECTION MODE: [0-" + str(len(CONN_OPT) - 1) + "]: ")
    opt = check_option(choice, min = 0, max = len(CONN_OPT) - 1)
    CONN_OPT.get(opt)[1]()
    terminate()