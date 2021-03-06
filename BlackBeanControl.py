#!python2

import broadlink, configparser
import sys, getopt
import time, binascii
import netaddr
import Settings
from os import path
from Crypto.Cipher import AES

SettingsFile = configparser.ConfigParser()
SettingsFile.optionxform = str
SettingsFile.read(Settings.BlackBeanControlSettings)

SentCommand = ''
ReKeyCommand = False
DeviceName=''
DeviceIPAddress = ''
DevicePort = ''
DeviceMACAddres = ''
AlternativeIPAddress = ''
AlternativePort = ''
AlternativeMACAddress = ''

try:
    Options, args = getopt.getopt(sys.argv[1:], 'c:d:r:i:p:m:h', ['command=','device=','rekey=','ipaddress=','port=','macaddress=','help'])
except getopt.GetoptError:
    print('BlackBeanControl.py -c <Command name> [-d <Device name>] [-i <IP Address>] [-p <Port>] [-m <MAC Address>] [-r <Re-Key Command>]')
    sys.exit(2)

for Option, Argument in Options:
    if Option in ('-h', '--help'):
        print('BlackBeanControl.py -c <Command name> [-d <Device name>] [-i <IP Address>] [-p <Port>] [-m <MAC Address>] [-r <Re-Key Command>]')
        sys.exit()
    elif Option in ('-c', '--command'):
        SentCommand = Argument
    elif Option in ('-d', '--device'):
        DeviceName = Argument
    elif Option in ('-r', '--rekey'):
        ReKeyCommand = True
        SentCommand = Argument
    elif Option in ('-i', '--ipaddress'):
        AlternativeIPAddress = Argument
    elif Option in ('-p', '--port'):
        AlternativePort = Argument
    elif Option in ('-m', '--macaddress'):
        AlternativeMACAddress = Argument

if SentCommand.strip() == '':
    print('Command name parameter is mandatory')
    sys.exit(2)

if (DeviceName.strip() != '') and ((AlternativeIPAddress.strip() != '') or (AlternativePort.strip() != '') or (AlternativeMACAddress.strip() != '')):
    print('Device name parameter can not be used in conjunction with IP Address/Port/MAC Address parameters')
    sys.exit(2)

if (((AlternativeIPAddress.strip() != '') or (AlternativePort.strip() != '') or (AlternativeMACAddress.strip() != '')) and ((AlternativeIPAddress.strip() == '') or (AlternativePort.strip() == '') or (AlternativeMACAddress.strip() == ''))):
    print('IP Address, Port and MAC Address parameters can not be used separately')
    sys.exit(2)

if DeviceName.strip() != '':
    if SettingsFile.has_section(DeviceName.strip()):
        if SettingsFile.has_option(DeviceName.strip(), 'IPAddress'):
            DeviceIPAddress = SettingsFile.get(DeviceName.strip(), 'IPAddress')
        else:
            DeviceIPAddress = ''

        if SettingsFile.has_option(DeviceName.strip(), 'Port'):
            DevicePort = SettingsFile.get(DeviceName.strip(), 'Port')
        else:
            DevicePort = ''

        if SettingsFile.has_option(DeviceName.strip(), 'MACAddress'):
            DeviceMACAddress = SettingsFile.get(DeviceName.strip(), 'MACAddress')
        else:
            DeviceMACAddress = ''
    else:
        print('Device does not exist in BlackBeanControl.ini')
        sys.exit(2)

if (DeviceName.strip() != '') and (DeviceIPAddress.strip() == ''):
    print('IP address must exist in BlackBeanControl.ini for the selected device')
    sys.exit(2)

if (DeviceName.strip() != '') and (DevicePort.strip() == ''):
    print('Port must exist in BlackBeanControl.ini for the selected device')
    sys.exit(2)

if (DeviceName.strip() != '') and (DeviceMACAddress.strip() == ''):
    print('MAC address must exist in BlackBeanControl.ini for the selected device')
    sys.exit(2)

if DeviceName.strip() != '':
    RealIPAddress = DeviceIPAddress.strip()
elif AlternativeIPAddress.strip() != '':
    RealIPAddress = AlternativeIPAddress.strip()
else:
    RealIPAddress = Settings.IPAddress

if RealIPAddress.strip() == '':
    print('IP address must exist in BlackBeanControl.ini or it should be entered as a command line parameter')
    sys.exit(2)

if DeviceName.strip() != '':
    RealPort = DevicePort.strip()
elif AlternativePort.strip() != '':
    RealPort = AlternativePort.strip()
else:
    RealPort = Settings.Port

if RealPort.strip() == '':
    print('Port must exist in BlackBeanControl.ini or it should be entered as a command line parameter')
    sys.exit(2)
else:
    RealPort = int(RealPort.strip())

if DeviceName.strip() != '':
    RealMACAddress = DeviceMACAddress.strip()
elif AlternativeMACAddress.strip() != '':
    RealMACAddress = AlternativeMACAddress.strip()
else:
    RealMACAddress = Settings.MACAddress

if RealMACAddress.strip() == '':
    print('MAC address must exist in BlackBeanControl.ini or it should be entered as a command line parameter')
    sys.exit(2)
else:
    RealMACAddress = netaddr.EUI(RealMACAddress)

RM3Device = broadlink.rm((RealIPAddress, RealPort), RealMACAddress)
RM3Device.auth()

if ReKeyCommand:
    if SettingsFile.has_option('Commands', SentCommand):
        CommandFromSettings = SettingsFile.get('Commands', SentCommand)

        if CommandFromSettings[0:4] != '2600':
            RM3Key = RM3Device.key
            RM3IV = RM3Device.iv

            DecodedCommand = binascii.unhexlify(CommandFromSettings)
            AESEncryption = AES.new(str(RM3Key), AES.MODE_CBC, str(RM3IV))
            EncodedCommand = AESEncryption.encrypt(str(DecodedCommand))
            FinalCommand = EncodedCommand[0x04:]
            EncodedCommand = FinalCommand.encode('hex')

            BlackBeanControlIniFile = open(path.join(Settings.ApplicationDir, 'BlackBeanControl.ini'), 'w')
            SettingsFile.set('Commands', SentCommand, EncodedCommand)
            SettingsFile.write(BlackBeanControlIniFile)
            BlackBeanControlIniFile.close()
            sys.exit()
        else:
            print("Command appears to already be re-keyed.")
            sys.exit(2)
    else:
        print("Command not found in ini file for re-keying.")
        sys.exit(2)


if SettingsFile.has_option('Commands', SentCommand):
    CommandFromSettings = SettingsFile.get('Commands', SentCommand)
else:
    CommandFromSettings = ''

if CommandFromSettings.strip() != '':
    DecodedCommand = CommandFromSettings.decode('hex')
    RM3Device.send_data(DecodedCommand)
else:
    RM3Device.enter_learning()
    LearnedCommand = RM3Device.check_data()

    while LearnedCommand is None:
        LearnedCommand = RM3Device.check_data()

    EncodedCommand = LearnedCommand.encode('hex')

    BlackBeanControlIniFile = open(path.join(Settings.ApplicationDir, 'BlackBeanControl.ini'), 'w')    
    SettingsFile.set('Commands', SentCommand, EncodedCommand)
    SettingsFile.write(BlackBeanControlIniFile)
    BlackBeanControlIniFile.close()
    
