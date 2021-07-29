import struct

# Twisted Imports
from twisted.internet import defer
from twisted.internet.protocol import Factory

# Package Imports
from octopus.util import now
from octopus.machine import Machine, Stream, Property
from octopus.protocol.basic import QueuedLineReceiver

# Twisted Imports
from twisted.python import log


#
# Serial Settings for EL-PRESS
# -----------------------------------
#
# Baud rate 38400 bps
# Data bits 8         Parity       None
# Stop bits 1         Flow control None
#
# Protocol type   Raw TCP
#
# On/Off
# -----------------------------------------------
# Set control mode RS232        :058001010400\r\n
# Set controller to 0%          :05800101040C\r\n
#
# Get measurement data
# -----------------------------------------------
# Measure                       :06800401210120\r\n
#
# Setpoint
# -----------------------------------------------
# 

def hex_setpoint(x):
    return f'{(int((x - 0) * (32000 - 0) / (100 - 0) + 0)):04x}'

def hex_measurement(x):
    val = int(x, 16)
    return float((val - 0) * (100 - 0) / (32000 - 0) + 0)

def float_to_hex(f):
    hex_result = struct.unpack('<I', struct.pack('<f', f))[0]
    return f'{hex_result:08x}'

def hex_to_float(h):
    return struct.unpack('!f', bytes.fromhex(h))[0]

class ElPress(Machine):

    protocolFactory = Factory.forProtocol(QueuedLineReceiver)
    name = "Bronkhorst EL-PRESS"

    def setup (self):

        # setup variables
        self.power = Property(title = "Power", type = str, options = ("on", "off"), setter = _set_power(self))
        self.percentage_setpoint = Property(title = "Setpoint", type = float, unit = "%", setter = _set_percentage_setpoint(self))
        self.pressure_setpoint = Property(title = "Setpoint", type = float, unit = "bar", setter = _set_pressure_setpoint(self))
        
        self.percentage_pressure = Stream(title = "Flow rate", type = float, unit = "%")
        self.pressure = Stream(title = "Flow rate", type = float, unit = "bar")

    def start (self):
       
        def interpret_percentage_pressure (result: str):
            val = result[-4:]
            return hex_measurement(val)

        def interpret_pressure (result: str):
            val = result[-8:]
            return hex_to_float(val)
        
        to_monitor = []

        def addMonitor (command, fn, variable: Stream):
            def interpret (result):
                variable._push(fn(result), now())
            
            to_monitor.append(( command, interpret ))

        addMonitor(":06800401210120", interpret_percentage_pressure, self.percentage_pressure)
        addMonitor(":06800421402140", interpret_pressure, self.pressure)

        def monitor ():
            for cmd, fn in to_monitor:
                self.protocol.write(cmd).addCallback(fn)

        self._monitor = self._tick(monitor, 1)

    def stop (self):
        if self._monitor:
            self._monitor.stop()

    def reset (self):
        return defer.succeed('OK')

def _set_power (machine: ElPress):
    @defer.inlineCallbacks
    def set_power (power: str):
        power_char = '00' if power == 'on' else '0C'
        result = yield machine.protocol.write(
            f":0580010104{power_char}"
        )

        if result != ':0480000004':
            raise Exception(f"Could not switch {power} EL-PRESS power")

        machine.power._push(power)
        return 'OK'

    return set_power

def _set_percentage_setpoint (machine: ElPress):
    @defer.inlineCallbacks
    def set_percentage_setpoint (setpoint: float):
        log.err("Hi")
        log.err(setpoint)
        val = hex_setpoint(setpoint)
        log.err(val)
        result = yield machine.protocol.write(f":0680010121{val}")
        machine.percentage_setpoint._push(setpoint)

        if result != ':0480000005':
            raise Exception(f"Could not set EL-PRESS setpoint to {setpoint}")

        return "OK"

    return set_percentage_setpoint

def _set_pressure_setpoint (machine: ElPress):
    @defer.inlineCallbacks
    def set_pressure_setpoint (setpoint: float):
        val = float_to_hex(setpoint)
        result = yield machine.protocol.write(f":0880012143{val}")
        machine.pressure_setpoint._push(setpoint)

        if result != ':0480000007':
            raise Exception(f"Could not set EL-PRESS setpoint to {setpoint}")

        return "OK"

    return set_pressure_setpoint