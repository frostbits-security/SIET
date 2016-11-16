# SIET
Smart Install Exploitation Tool

Smart Install is a plug-and-play configuration and image-management feature that provides zero-touch deployment for new switches. You can ship a switch to a location, place it in the network and power it on with no configuration required on the device.

You can easy identify it by nmap: 
nmap -n -Pn -p 4786 -v 192.168.0.1

This protocol have few security issue.
The first one allows to change tftp-server address on client device by sending one malformed tcp packet.
The second issue allows to copy client's startup-config on tftp-server exchanged previously.
The third issue allows to substitute client's startup-config for the file which has been copied and edited. Next, the device will reboot in defined time.
The fourth allows to upgrade ios image on the "client" device.
The fifth is a new feature working only at 3.6.0E and 15.2(2)E ios versions. It allows to execute random set of commands on the "client" device.

All of them are caused by the lack of any authentication in smart install protocol. Any device can act as a director and send malformed tcp packet. It works on any "client" devices where smart install is enable. Not matter used smart install in network or not.

This simple tool help's you to use all of them.

Syntax: sudo python siet.py -h -i 192.168.0.1 
t - test device for smart install.
g -get device config.
c - change device config.
u - update device IOS.
e - execude commands in device console.
