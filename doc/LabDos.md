## Serial Settings

```
Baud Rate - 9600
Parity - None
Data Bits - 8
Stop Bits - 2
Flow Control - None
```

## Serial Commands
```
Description - Current Speed
Command - IN_PV_00\r\n
Unit - RPM
Reply - IN_PV_00 00100\r\n
Value - 1 RPM
```
```
Description - Set Speed
Command - OUT_SP_00 +00100\r\n
Unit - RPM
Reply - OUT_SP_00 +00100\r\n
Value - 1 RPM
```
```
Description - Turn On/Off
Command - OUT_MODE_00 0\r\n (1 for on)
Unit - On/Off
Reply - OUT_MODE_00 0\r\n
Value - Off
```