#This plugin for Loxberry (https://wiki.loxberry.de/) is used to simulate a Fronius SmartMeter with MODBUS RTU protocol.



#Known Issues
For me, Modbus communication always breaks off after days at around 2:00 p.m. - 3:00 p.m. and only comes back automatically two days later. I suspect a problem with my Pi and am relying on experience from the field to see whether this also occurs for other users. A cron job that restarts the script every day at 00:01 seems to help for me.
