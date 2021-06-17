# Twisted Imports
from twisted.internet import defer
from twisted.internet.protocol import Factory

# Package Imports
from ..machine import Machine, Stream, ui, Property
from ..util import now
from ..protocol.basic import QueuedLineReceiver

__all__ = ["PCB", "EWBalance"]


class PCB (Machine):

    protocolFactory = Factory.forProtocol(QueuedLineReceiver)
    name = "Kern PCB Balance"

    def setup (self):

        # setup variables
        self.weight = Stream(title = "Weight", type = float, unit = "g")

        self.ui = ui(
            traces = [],
            properties = [
                self.weight
            ]
        )

    def start (self):
        # setup monitor on a tick to update variables

        def interpret_weight (result):
            if result == "           Error":
                # raise some error
                return

            if result[1] == "-":
                result = - float(result[2:12].strip())
            else:
                result = float(result[1:12].strip())

            self.weight._push(result, now())

        def monitor_weight ():
            self.protocol.write("w").addCallback(interpret_weight)

        self._tick(monitor_weight, 1)

    def stop (self):
        self._stopTicks()

    def reset (self):
        return defer.succeed('OK')

    def getStableWeight (self):
        d = defer.Deferred()

        def interpret (result):
            result = result.strip()

            if result == "Error":
                raise Exception("Error fetching stable weight")
            else:
                return result

        self.protocol.write("s").addCallback(interpret).chainDeferred(d)

        return d

    def tare (self):
        return self.protocol.write("t", expectReply = False, wait = 5)

class EWBalance (Machine):

    protocolFactory = Factory.forProtocol(QueuedLineReceiver)
    name = "Kern EW Balance"

    def setup (self):

        # setup variables
        self.weight = Stream(title = "Weight", type = float, unit = "g")
        self.status = Property(title = "Status", type = "str")

    def start (self):
        def interpret_weight (result: str):
            result_state = result[-1]
            # result_type = result[-2]
            result_unit = result[-4:2]

            if result_state == "E":
                self.status._push("error")
                return
            elif result_state == "S":
                self.status._push("stable")
            elif result_state == "U":
                self.status._push("fluctuating")

            # result_type != "G" --> out of range.
            
            if result_unit != " G":
                raise Exception("Balance units should be set to grams.")

            result_value = float(result[:-5])

            self.weight._push(result_value)

        def monitor_weight ():
            self.protocol.write("O8").addCallback(interpret_weight)

        self._tick(monitor_weight, 1)

    def stop (self):
        self._stopTicks()

    def reset (self):
        return defer.succeed('OK')

    def tare (self):
        return self.protocol.write("T ", expectReply = False, wait = 5)
