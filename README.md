This plugin for Loxberry (https://wiki.loxberry.de/) is used to simulate a Fronius SmartMeter with MODBUS RTU protocol.

Note: Text below is automaticaly translated due to lack of time :-) - so please be lenitent.

NOTE: 
Due to the fact that Fronius changed their inverter firmware to open for Modbus TCP meters, this RTU version is not needed any more very often.
So I will reduce my work regarding RTU and focus on the TCP version "fronius_sm_simulator_tcp".
Everyone who want's to proceed work with RTU is welcome :-)

Functional Description
======================
The plugin simulates a Fronius Smart Meter in the Modbus RTU network. This means that consumption values can be received via MQTT and forwarded to a Fronius inverter (e.g.: Symo, Symo Hybrid). The data is then permanently stored in the Solarweb statistics.

Installation
============
Installation wie üblich als ZIP über die Loxberry Installationsroutine.
Die Installation kann je nach verwendeten Pi bis zu 20 Minuten dauern

Prerequisites
=============
Ein bereits vorhandener SmartMeter, welcher ausgelesen werden kann und dessen Daten via MQTT übertragen werden können.
Ein Modbus Modul für den Raspberry
Plugin "MQTT Gateway" muss installiert und konfiguriert sein.

Configuration
=============
MQTT Topic current consumption: current consumption (current power) in watts (W)
MQTT Topic Purchase (absolute value): current meter reading for purchased energy in watt hours (Wh)
MQTT Topic Feed-in (absolute value): current meter reading for fed-in energy in watt hours (Wh)
Correction factor: If the data is delivered in kWh via MQTT, it must be converted into Wh =⇒ Correction factor 1000 (default setting).
Port of the Modbus adapter: Port where the Modbus adapter is plugged in.

!!! WARNING !!!
===============
The Fronius inverter does NOT use the "current power in watts" to calculate the current consumption and fill the statistics, but rather calculates this information itself using the difference between the absolute values of the purchase and feed-in in the time window of the query. The data MUST be provided via MODBUS in watt hours (see correction factor description above). If an error occurs when choosing the correction factor, the statistics in the data manager will be falsified.

A falsified statistic can no longer be changed independently!

Of course, this happened to me during my development attempts because I had no idea how the data had to be provided and could only have the statistics corrected by Fronius Support.

Known Issues
============
Modbus communication always stopps after days at around 2:00 p.m. - 3:00 p.m. and only comes back automatically two days later. I suspect a problem with my Pi and am relying on experience from the field to see whether this also occurs for other users. A cron job that restarts the script every day at 00:01 seems to help for me.

Roadmap
=======
Extension to simulate multiple meters: Goal 1. Primary meter (consumption) and other secondary meters for e.g.: Integration of other energy sources (wind turbine, CHP, PV without Fronius inverter, ...)
Improving usability (web interface)
Upgrade to Python3
DEBUG functions must be implemented
Plausibility check of the data regarding kWh ⇔ Wh to avoid statistical problems.
Leaving BETA status :-)
