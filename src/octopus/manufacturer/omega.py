import logging
from itertools import groupby

# Twisted Imports
from twisted.internet import defer
from twisted.internet.protocol import Factory
from twisted.python import log

# Package Imports
from ..machine import Machine, Stream, ui
from ..util import now
from ..protocol.basic import VaryingDelimiterQueuedLineReceiver, LineOnlyReceiver

__all__ = ["HH306A", "RDXL4SD"]


# Connection: 9600, 8N1
class HH306A (Machine):

    protocolFactory = Factory.forProtocol(VaryingDelimiterQueuedLineReceiver)
    name = "Omega HH306A Thermometer Data Logger"

    def setup (self):

        # setup variables
        self.temp1 = Stream(title = "Temperature 1", type = float, unit = "C")
        self.temp2 = Stream(title = "Temperature 2", type = float, unit = "C")

        self.ui = ui(
            traces = [],
            properties = [
                self.temp1,
                self.temp2
            ]
        )

    @defer.inlineCallbacks
    def start (self):
        # Set protocol defaults
        self.protocol.send_delimiter = ''
        self.protocol.start_delimiter = '\x02'
        self.protocol.end_delimiter = '\x03'

        # Check that the correct device is connected
        model_no = yield self.protocol.write(
            "K",
            length = 3,
            start_delimiter = '',
            end_delimiter = '\r'
        )

        if model_no != "306":
            raise Exception("HH306A: Expected model '306', received '{:s}'".format(model_no))

        data = yield self.protocol.write("A", length = 8)
        info = [(ord(data[0]) & (1 << i)) > 0 for i in range(8)]

        # Check if in MAX/MIN mode:
        if info[1] or info[2]:
            yield self.protocol.write("N", expect_reply = False)

        # Check if displaying time:
        if info[3]:
            yield self.protocol.write("T", expect_reply = False)

        # Check if in HOLD mode:
        if info[5]:
            yield self.protocol.write("H", expect_reply = False)

        def interpret_data (result):
            byte_2 = ord(result[0])
            byte_3 = ord(result[1])

            showing_time = byte_2 & 8 > 0
            in_f = byte_2 & 128 == 0

            t1_sign = -1 if (byte_3 & 2 > 0) else 1
            t1_factor = 1.0 if (byte_3 & 4 > 0) else 0.1

            t1 = (
                (int(hex(ord(result[2]))[2:].strip('b')) * 100) +
                int(hex(ord(result[3]))[2:].strip('b'))
            ) * t1_factor * t1_sign

            if not showing_time:
                t2_sign = -1 if (byte_3 & 16 > 0) else -1
                t2_factor = 1.0 if (byte_3 & 32 > 0) else 0.1
                t2 = (
                (int(hex(ord(result[6]))[2:].strip('b')) * 100) +
                int(hex(ord(result[7]))[2:].strip('b'))
            ) * t2_factor * t2_sign

                if in_f:
                    t2 = round((t2 - 32.0) * 5.0 / 9.0, 1)

                self.temp2._push(t2)

            if in_f:
                t1 = round((t1 - 32.0) * 5.0 / 9.0, 1)

            self.temp1._push(t1)

        def monitor ():
            return self.protocol.write(
                "A",
                length = 8
            ).addCallback(interpret_data).addErrback(log.err)

        yield monitor()

        self._tick(monitor, 1)

    def stop (self):
        self._stopTicks()

#
# Serial Settings for RDXL4SD
# -----------------------------------
#
# Baud rate 9600 bps
# Data bits 8         Parity       None
# Stop bits 1         Flow control None
#
# Protocol type   Raw TCP
#
# Sample Data
# -----------------------------------
# 41010100000223
#
# Broken Down
# -----------------------------------
# 4
# 1 - Thermocouple port
# 01 - UoM 01=C 02=F
# 0 - Polarity
# 1 - Decimal point
# 00000223 - Reading

class PrintLineReceiver (LineOnlyReceiver):
    delimiter = b"\r"
    val_list = [0,0,0,0]
    val_updated = [False, False, False, False]

    def __init__ (self):
        self.listener = None

    def setListener (self, listener):
        self.listener = listener

    def lineReceived (self, line: bytes):
        line = line.replace(b'\x02', b'').replace(b'\x18', b'0').decode()

        thermocouple_port = int(line[1])-1
        thermocouple_uom = int(line[2:4])
        thermocouple_polarity = line[4]
        thermocouple_dp = int(line[5])
        thermocouple_val = line[6:len(line)]

        treated_val = float(thermocouple_val[0:len(thermocouple_val)-thermocouple_dp] + '.' + thermocouple_val[-thermocouple_dp])
        if thermocouple_polarity == 1:
            treated_val = -treated_val

        self.val_list[thermocouple_port] = treated_val
        self.val_updated[thermocouple_port] = True

        if self.listener is not None and all(self.val_updated):
            log.msg(self.val_list, logging.DEBUG)
            self.listener(self.val_list)
            self.val_updated = [False] * (len(self.val_updated))

class RDXL4SD(Machine):

    protocolFactory = Factory.forProtocol(PrintLineReceiver)
    name = "Omega RDXL4SD"

    def setup (self):

        # setup variables
        self.temp1 = Stream(title = "Temperature 1", type = float, unit = "C")
        self.temp2 = Stream(title = "Temperature 2", type = float, unit = "C")
        self.temp3 = Stream(title = "Temperature 3", type = float, unit = "C")
        self.temp4 = Stream(title = "Temperature 4", type = float, unit = "C")

    def start (self):
        def interpret_temperature (result):
            self.temp1._push(result[0])
            self.temp2._push(result[1])
            self.temp3._push(result[2])
            self.temp4._push(result[3])

        self.protocol.setListener(interpret_temperature)

    def stop (self):
        self._stopTicks()

    def reset (self):
        return defer.succeed('OK')