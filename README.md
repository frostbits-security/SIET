# SIET
Smart Install Exploitation Tool

tag: Cisco smart install exploit

Cisco Smart Install is a plug-and-play configuration and image-management feature that provides zero-touch deployment for new switches. You can ship a switch to a location, place it in the network and power it on with no configuration required on the device.

You can easy identify it using nmap: 
nmap -n -Pn -p 4786 -v 192.168.0.1

This protocol has a security issue that allows:

1. Change tftp-server address on client device by sending one malformed TCP packet.

2. Copy client's startup-config on tftp-server exchanged previously.

3. Substitute client's startup-config for the file which has been copied and edited. Device will reboot in defined time.

4. Upgrade ios image on the "client" device.

5. Execute random set of commands on the "client" device. IS a new feature working only at 3.6.0E and 15.2(2)E ios versions. 


All of them are caused by the lack of any authentication in smart install protocol. Any device can act as a director and send malformed tcp packet. It works on any "client" device where smart install is enabled. It does not matter if it used smart install in the network or not.

**Confim** from vendor: https://tools.cisco.com/security/center/content/CiscoSecurityResponse/cisco-sr-20170214-smi
                        https://tools.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-20160323-smi

**Slides**: https://2016.zeronights.ru/wp-content/uploads/2016/12/CiscoSmartInstall.v3.pdf

This simple tool helps you to use all of them.

Syntax: sudo python siet.py **-h** -i 192.168.0.1

  -t  test device for smart install.
  
  -g  get device config.
  
  -c  change device config.
  
  -u  update device IOS.
  
  -e  execude commands in device console.




SIET2 have new option "-l". You can use list of ip addresses for getting configuration file.

Example of usage: **sudo python siet2.1.py -l list.txt -g**

SIET2 not fully tested.
