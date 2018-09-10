#!/usr/bin/env python
#IMPORTANT!!! - You may use this script as superuser

import os
import sys
import logging
import binascii
import pygatt
from io import BytesIO
import msgpack 

#You must choose an obtion between public and random
ADDRESS_TYPE = pygatt.BLEAddressType.public
#ADDRESS_TYPE = pygatt.BLEAddressType.random

#Menu options
SELECT_DEVICE   = 0
SELECT_SERVICE  = 1
SELECT_OPTION   = 2

#Methods in service
CHAR_READ   = 0
CHAR_WRITE  = 1
CHAR_EXIT   = 2


logging.basicConfig()
logging.getLogger('pygatt').setLevel(logging.INFO)


def check_input(input, min=0, max=100):
    try:
        return int(input) if min <= int(input) and int(input)<=max else -1
    except:
        print("ERROR you must introduce a valid option: 0-" +str(max)+"]")
        return



def print_menu(menu, devices =None):  ## Your menu design here
    
    if menu==SELECT_DEVICE:
        i=0
        print(29 * "-"+ "DEVICES"+ 29 * "-")
        for device in devices:
            print('\t-'+str(i)+' ADDRESS: '+ device['address'] +( ", NAME: "+device['name'] if  device['name']!=None else ""))
            i+=1
        print("\t-"+str(i)+" EXIT")
        print(67 * "-")
        correct = False
        while not correct:
            choice = raw_input("-SELECT DEVICE: [0-" +str(i) +"]: ")
            input = check_input( choice, min= 0,max = i)
            if input==i:
                adapter.stop()
                exit(1)
            elif input>-1:
                correct=True
                return devices[int(choice)]

    elif menu==SELECT_SERVICE:
        print(20 * "-"+ "SERVICES AVAILABLES"+ 20 * "-")
        i=0
        for uuid in devices.discover_characteristics().keys():
            print '\t-'+str(i)+' Service uuid: '+ str(uuid)
            i+=1
        print("\t-"+str(i)+" EXIT")
        print(67 * "-")
        correct = False
        while not correct:
            choice = raw_input("-SELECT SERVICE UUID: [0-" +str(i) +"]: ")
            input = check_input( choice, min= 0,max = i)
            
            if input==i:
                adapter.stop()
                exit(1)
            elif input>-1:
                correct=True
                return devices.discover_characteristics().keys()[input]

    elif menu==SELECT_OPTION:
        print(30 * "-"+ "MENU"+ 30 * "-")
        print(str(CHAR_READ)+". Read characteristic")
        print(str(CHAR_WRITE)+". Write characteristic")
        print(str(CHAR_EXIT)+". Disconnect and exit")
        print(67 * "-")
    

def read(device, uuid):
    try:
        print("-Read UUID %s: "% (uuid))
        response = device.char_read(uuid)
        print("\n\t-Value: %s\n" % (response))
        print("\n\t--Response %s") % msgpack.unpackb(response, raw=False)

    except:
        print("-ERROR: Couldn't read the characteristic of UUID %s", uuid)
        
def write(device, uuid):
    n = raw_input("Hoy many attributes you want to write?: ")
    message=[]
    for i in range(int(n)):
        message.append(raw_input("Key: "))
        message.append(raw_input("Value: "))
    packed = msgpack.packb(message, use_bin_type=True)
    print msgpack.unpackb(packed)
    device.char_write(uuid, bytearray(packed))

def handle_data(handle, value):
    """
    handle -- integer, characteristic read handle the data was received on
    value -- bytearray, the data returned in the notification
    """
    print("---Received data: %s" % binascii.hexlify(value))


if __name__ == '__main__':
  
    adapter = pygatt.GATTToolBackend(hci_device="hci0")
    adapter.start()
    devices = adapter.scan(run_as_root=True, timeout=3)
    device = print_menu(SELECT_DEVICE, devices = devices)
    address=device['address']
    try:
        print("Connecting...")
        device = adapter.connect(address, address_type=ADDRESS_TYPE)
        print("Connected")
        service_uuid = print_menu(SELECT_SERVICE,device)
        device.subscribe(service_uuid,callback = handle_data)
        loop =True
        while loop:

            print_menu(SELECT_OPTION)
            choice = raw_input("Enter your choice [0-"+str(CHAR_EXIT)+"]: ")
            check_input(min,max,choice)
            if int(choice) == CHAR_READ:
                print("Read characteristic:\n\t")
                read(device, service_uuid)

            elif int(choice) == CHAR_WRITE:
                print("Write characteristic")
                write(device ,service_uuid)

            else:
                device.disconnect()
                loop = False

    except pygatt.exceptions.NotConnectedError:
        print("failed to connect to %s" % address)
            

    adapter.stop()
    sys.exit(1)