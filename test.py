from octopus.manufacturer import sartorious
from octopus.transport.basic import serial

serial_connection = serial("/dev/ttyACM0", baudrate=9600)
bal = sartorious.Sartorious(serial_connection)
bal.weight

