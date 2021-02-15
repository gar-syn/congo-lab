# Twisted Imports
from twisted.internet import defer
from twisted.internet.protocol import Factory

# Package Imports
from octopus.util import now
from octopus.machine import Machine, Stream, Property
from octopus.protocol.basic import QueuedLineReceiver


#
# Serial Settings for SyrDos / LabDos
# -----------------------------------
#
# Baud rate 9600 bps
# Data bits 8         Parity       None
# Stop bits 1         Flow control None
#
# Protocol type   Raw TCP
#

class HMP4040(Machine):

    protocolFactory = Factory.forProtocol(QueuedLineReceiver)
    name = "Rohde & Schwarz HMP4040"

    def setup (self):

        # setup variables
        self.channel = Property(title = "Set Channel", type = int, setter = _set_channel(self))
        self.activate = Property(title = "Activate Channel", type = int, setter = _set_activate(self))
        self.voltage = Property(title = "Set Voltage", type = float, unit = "Volt", setter = _set_voltage(self))
        self.current = Property(title = "Set Current", type = float, unit = "Amp", setter = _set_current(self))
        
        self.get_volt1 = Stream(title = "Ch1 V", type = float, unit = "Volt")
        self.get_amp1 = Stream(title = "Ch1 A", type = float, unit = "Amp")
        self.get_volt2 = Stream(title = "Ch2 V", type = float, unit = "Volt")
        self.get_amp2 = Stream(title = "Ch2 A", type = float, unit = "Amp")
        self.get_volt3 = Stream(title = "Ch3 V", type = float, unit = "Volt")
        self.get_amp3 = Stream(title = "Ch3 A", type = float, unit = "Amp")
        self.get_volt4 = Stream(title = "Ch4 V", type = float, unit = "Volt")
        self.get_amp4 = Stream(title = "Ch4 A", type = float, unit = "Amp")

    def start (self):

        def interpret_voltage (result: str) -> float:
            return float(result)
        
        def interpret_voltage (result: str) -> float:
            return float(result)

        to_monitor = []

        def addMonitor (command, fn, variable: Stream):
            def interpret (result):
                variable._push(fn(result), now())
            
            to_monitor.append(( command, interpret ))

        addMonitor("INST OUT1\r\nVOLT?", interpret_voltage, self.get_volt1)
        addMonitor("INST OUT1\r\nCURR?", interpret_amps, self.get_amp1)
        # addMonitor("INST OUT2\r\nVOLT?", interpret_voltage, self.get_voltage2)
        # addMonitor("INST OUT2\r\nCURR?", interpret_amps, self.get_amp2)
        # addMonitor("INST OUT3\r\nVOLT?", interpret_voltage, self.get_voltage3)
        # addMonitor("INST OUT3\r\nCURR?", interpret_amps, self.get_amp3)
        # addMonitor("INST OUT4\r\nVOLT?", interpret_voltage, self.get_voltage4)
        # addMonitor("INST OUT4\r\nCURR?", interpret_amps, self.get_amp4)

        def monitor ():
            for cmd, fn in to_monitor:
                self.protocol.write(cmd).addCallback(fn)

        self._monitor = self._tick(monitor, 1)

    def stop (self):
        if self._monitor:
            self._monitor.stop()

    def reset (self):
        return defer.succeed('OK')

def _set_channel (machine: HMP4040):
    def set_channel (setpoint: int):
        return machine.protocol.write(f"INST OUT{setpoint}", expectReply = False)

    return set_channel

def _set_activate (machine: HMP4040):
    def set_activate (setpoint: int):
        return machine.protocol.write(f"OUTP:SEL {setpoint}", expectReply = False)

    return set_activate

def _set_voltage (machine: HMP4040):
    def set_voltage (setpoint: float):
        return machine.protocol.write(f"VOLT {setpoint:.3f}", expectReply = False)

    return set_voltage

def _set_current (machine: HMP4040):
    def set_current (setpoint: float):
        return machine.protocol.write(f"CURR {setpoint:.3f}", expectReply = False)

    return set_current