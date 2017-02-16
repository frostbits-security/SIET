# SIET
Smart Install Exploitation Tool

Cisco Smart Install is a plug-and-play configuration and image-management feature that provides zero-touch deployment for new switches. You can ship a switch to a location, place it in the network and power it on with no configuration required on the device.

You can easy identify it by nmap: 
nmap -n -Pn -p 4786 -v 192.168.0.1

This protocol have few security issue, that allows:

1. Change tftp-server address on client device by sending one malformed tcp packet.

2. Copy client's startup-config on tftp-server exchanged previously.

3. Substitute client's startup-config for the file which has been copied and edited. Device will reboot in defined time.

4. Upgrade ios image on the "client" device.

5. Execute random set of commands on the "client" device. IS a new feature working only at 3.6.0E and 15.2(2)E ios versions. 


All of them are caused by the lack of any authentication in smart install protocol. Any device can act as a director and send malformed tcp packet. It works on any "client" devices where smart install is enable. Not matter used smart install in network or not.

This simple tool help's you to use all of them.

Syntax: sudo python siet.py **-h** -i 192.168.0.1

  -t  test device for smart install.
  -g  get device config.
  -c  change device config.
  -u  update device IOS.
  -e  execude commands in device console.

==========================================================================================================================
SIET2 have new option "-l". You can use list of ip addresses for getting configuration file.
Example of usage: **python siet2.1.py -l list.txt -g**

Example of list file:
172.16.0.1
172.17.4.1
...
172.25.1.20

SIET2 not fully tested
