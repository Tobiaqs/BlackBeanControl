#!python2

import broadlink, configparser
import sys, getopt
import time, binascii
import netaddr
import Settings
from os import path
from Crypto.Cipher import AES

RM3Device = broadlink.rm(("192.168.1.100", 80), netaddr.EUI("B4:43:0D:FC:05:CE"))
RM3Device.auth()

RM3Device.enter_learning()
PreviousCommand = None
while True:
    LearnedCommand = RM3Device.check_data()
    if LearnedCommand is not None:
        PreviousCommand = LearnedCommand.encode('hex')
        print(PreviousCommand)
        print("")
        RM3Device.enter_learning()
    time.sleep(0.1)
