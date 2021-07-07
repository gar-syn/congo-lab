# Twisted Imports
from twisted.internet import defer
from twisted.internet.protocol import Factory

# Package Imports
from octopus.util import now
from octopus.machine import Machine, Stream, Property
from octopus.protocol.basic import QueuedLineReceiver

#
# Serial Settings for Sartorious Balance
# -----------------------------------
#
# Baud rate 9600 bps
# Data bits 8         Parity       None
# Stop bits 2         Flow control None
#
# Protocol type   Raw TCP
#
# Example Reply
# G     +     0.04 g  ␍␊
# G     +    29.58 g  ␍␊
# G     +   107.39 g  ␍␊
# G     +  1158.47 g  ␍␊

class Sartorious (Machine):

    protocolFactory = Factory.forProtocol(QueuedLineReceiver)
    name = "Sartorious Balance"

    def setup (self):

        # setup variables
        self.weight = Stream(title = "Weight", type = float, unit = "g")

    def start (self):
        def interpret_weight (result: str):
            result_unit = result[-3:]

            if result_unit != "g":
                raise Exception("Balance units should be set to grams.")

            result_value = float((result[-14:-4]).replace(" ", ""))

            self.weight._push(result_value)

        def monitor_weight ():
            self.protocol.write("P").addCallback(interpret_weight)

        self._tick(monitor_weight, 1)

    def stop (self):
        self._stopTicks()

    def reset (self):
        return defer.succeed('OK')

    def tare (self):
        return self.protocol.write("T", expectReply = False, wait = 5)
