import socket
import struct
import json

import xml.etree.ElementTree as ET


import shure

MCAST_GRP = '239.255.254.253'
MCAST_PORT = 8427


rx_types = ['UHFR','QLXD','ULXD','AXTD']

deviceList = {}

discovered = {}

# https://stackoverflow.com/questions/603852/multicast-in-python
def discover():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) #mac fix
    sock.bind(('', MCAST_PORT))  # use MCAST_GRP instead of '' to listen only
                                 # to MCAST_GRP, not all groups on MCAST_PORT
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    while True:
        data, (ip,_) = sock.recvfrom(1024)
        data = data.decode('UTF-8',errors="ignore")
        # print(data)
        type = rx_type(data)
        dcid = dcid_find(data)
        if type is not '':
            device = dcid_get(dcid)
            print('RX: {} at: {} DCID: {} BAND: {}'.format(type,ip,dcid,device['band']))
            add_rx(ip,type)

def add_rx(ip,rx_type):
    # rx = { 'ip': ip,
           # 'type': rx_type }
    discovered[ip] = { 'type': rx_type.lower() }

def rx_type(data):
    rx = ''
    for i in rx_types:
        if i in data:
            rx = i
    return rx

def dcid_find(data):
    dcid = ''
    data = data.split(',')
    for i in data:
        i = i.strip('()')

        if 'cd:' in i:
            i = i.split('cd:')[-1]
            dcid = i

    return dcid

def dcid_get(dcid):
    return deviceList[dcid]

def DCID_Parse_old():

    tree = ET.parse('DCIDMap.xml')
    root = tree.getroot()

    devices = root.findall('./MapEntry')

    for device in devices:
        key = device.find('Key').text
        model = device.find('ModelName').text
        dcid = []
        for dccid in device.find('DCIDList').iter('DCID'):
            try:
                band = dccid.attrib['band']
            except:
                band = ''
            dcid.append({'DCID': dccid.text, 'BAND': band })

        dev = {'model': model, 'dcid': dcid }
        deviceList[key] = dev

    print(deviceList)


def DCID_Parse(file):
    tree = ET.parse(file)
    root = tree.getroot()

    devices = root.findall('./MapEntry')

    for device in devices:
        model = device.find('Key').text
        model_name = device.find('ModelName').text
        dcid = []
        for dccid in device.find('DCIDList').iter('DCID'):
            try:
                band = dccid.attrib['band']
            except:
                band = ''

            dev = {'model': model,'model_name':model_name, 'band':band }
            deviceList[dccid.text] = dev

def dcid_save_to_file(file):
    with open(file,'w') as f:
        json.dump(deviceList,f, indent=2, separators=(',',': '), sort_keys=True)
        f.write('\n')

def dcid_restore_from_file(file):
    global deviceList
    with open(file,'r') as f:
        deviceList = json.load(f)

def updateDCIDmap(inputFile,outputFile):
    DCID_Parse(inputFile);
    dcid_save_to_file(outputFile)


def main():
    # updateDCIDmap('DCIDmap.xml','dcid.json')
    dcid_restore_from_file('dcid.json')
    discover()


if __name__ == '__main__':
    main()
