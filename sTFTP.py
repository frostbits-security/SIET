#!/usr/bin/env python
""" -= DvK =- TFTP server 2017(p), revamped on 2021 """
import sys
import os
import socket
from codecs import encode
from codecs import decode

TFTP_FILES_PATH = 'tftp'  # path to files for transfering
TFTP_SERVER_PORT = 69
TFTP_GET_BYTE = 1
TFTP_PUT_BYTE = 2
TFTP_SOCK_TIMEOUT = 180  # in sec
TFTP_MIN_DATA_PORT = 44000  # range of UDP data port
TFTP_MAX_DATA_PORT = 65000  # -//-
DEF_BLKSIZE = 512  # size of data block in TFTP-packet
ECHO_FILE_SIZE = 0xa00000  # count of loaded or transfering bytes for print log message about this process (10 Mb)
MAX_BLKSIZE = 0x10000
MAX_BLKCOUNT = 0xffff

python_version = sys.version_info[0]


def hex_encode(toEncode):
  """ Version-agnostic function to encode hex strings """
  enc = None
  if python_version == 2:
    enc = toEncode.encode('hex')
  elif python_version == 3:
    enc = encode(bytes(toEncode, 'ascii'), 'hex').decode()
  return enc


def hex_decode(toDecode):
  """ Version-agnostic function to encode hex strings """
  dec = None
  if python_version == 2:
    dec = toDecode.decode('hex')
  elif python_version == 3:
    dec = decode(toDecode, 'hex')
  return dec


def TftpServer(sBindIp, SocketTimeout):
  """ tftp stuff """
  print("-= DvK =- TFTP server 2017(p)")
  print("[INFO]: Creating directory.")
  try:
    os.mkdir('tftp')
    print("[INFO]: Directory created.")
  except OSError:
    print("[INFO]: Directory already exists.")
  print("[INFO]: Binding socket .. ")
  try:
    ConnUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ConnUDP.settimeout(SocketTimeout)
    ConnUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ConnUDP.bind((sBindIp, TFTP_SERVER_PORT))
  except socket.error as msg:
    print("[ERR]: {}".format(msg))
    return
  print("[INFO]: Socket bound successfully.")
  dPort = TFTP_MIN_DATA_PORT
  while True:
    try:
      buff, (raddress, rport) = ConnUDP.recvfrom(MAX_BLKSIZE)
      if python_version == 3:
        buff = buff.decode()
    except socket.timeout:
      pass
    except socket.error:
      return
    print("[INFO]: Connection from {}:{}".format(raddress, rport))
    sReq = ''
    tReq = ord(buff[1])
    if tReq == TFTP_GET_BYTE:
      sReq = 'get'
      fMode = 'r'
    if tReq == TFTP_PUT_BYTE:
      sReq = 'put'
      fMode = 'w'
    if len(sReq) == 0:
      print("[ERR]: Illegal TFTP request".format(tReq))
      sUdp = '\x00\x05\x00\x01Illegal TFTP request\x00'
      ConnUDP.sendto(sUdp, (raddress, rport))
      continue
    ss = buff[2:].split('\0')
    nFile = ss[0]
    sType = ss[1]
    print("[INFO]:[{}] {}ting file {} {}".format(raddress, sReq, nFile, sType))
    if (sType == 'octet'):
      fMode += 'b'
    try:
      f = open(TFTP_FILES_PATH + '/' + nFile, fMode)
    except IOError:
      print("[INFO]:[{}]:[{}] Error opening file: {}/{}".format(raddress, sReq, TFTP_FILES_PATH, nFile))
      sUdp = '\x00\x05\x00\x01Error open file\x00'
      ConnUDP.sendto(sUdp, (raddress, rport))
      continue
    try:
      ConnDATA = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      ConnDATA.settimeout(SocketTimeout)
      ConnDATA.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      ConnDATA.bind(('', dPort))
    except socket.error:
      print("[ERR]:[{}]:[{}] Error binding data port {}".format(raddress, sReq, dPort))
      sUdp = '\x00\x05\x00\x01Internal error\x00'
      ConnUDP.sendto(sUdp, (raddress, rport))
      f.close()
      continue
    print("[INFO]:[{}]:[{}] Success binding data port {}".format(raddress, sReq, dPort))
    dPort += 1
    if dPort == TFTP_MAX_DATA_PORT:
      dPort = TFTP_MIN_DATA_PORT
    child_pid = os.fork()
    if child_pid < 0:
      print("[ERR]:[{}]:[{}] Error forking new process".format(raddress, sReq))
      sUdp = '\x00\x05\x00\x01Internal error\x00'
      ConnUDP.sendto(sUdp, (raddress, rport))
      f.close()
      ConnDATA.close()
      continue
    if child_pid == 0:
      if sReq == 'put':
        sUdp = '0004' + ('%04x' % 0)
        ConnDATA.sendto(hex_decode(sUdp), (raddress, rport))
        fSize = 0
        buff, (raddress, rport) = ConnDATA.recvfrom(MAX_BLKSIZE)
        if python_version == 3:
          buff = buff.decode()
        while buff:
          fSize += len(buff[4:])
          if python_version == 2:
            f.write(buff[4:])
          elif python_version == 3:
            f.write(bytes(buff[4], 'ascii'))
          sUdp = '\x00\x04' + buff[2:4]
          if python_version == 2:
            ConnDATA.sendto(sUdp, (raddress, rport))
          elif python_version == 3:
            ConnDATA.sendto(bytes(sUdp, 'ascii'), (raddress, rport))
          if len(buff[4:]) < DEF_BLKSIZE:
            break
          buff, (raddress, rport) = ConnDATA.recvfrom(MAX_BLKSIZE)
          if python_version == 3:
            buff = buff.decode()
          if int(fSize / ECHO_FILE_SIZE) * ECHO_FILE_SIZE == fSize:
            print("[INFO]:[{}]:[{}] File {}/{} downloading, size: {}".format(
              raddress, sReq, TFTP_FILES_PATH, nFile, fSize))
        f.close()
        ConnDATA.close()
        print("[INFO]:[{}]:[{}] File {}/{} finished downloading, size: {}".format(
          raddress, sReq, TFTP_FILES_PATH, nFile, fSize))
        sys.exit(0)
      if sReq == 'get':
        data = f.read(DEF_BLKSIZE)
        fSize = len(data)
        j = 1
        while data:
          sUdp = hex_decode('0003' + ('%04x' % j)) + data
          if python_version == 2:
            ConnDATA.sendto(sUdp, (raddress, rport))
          elif python_version == 3:
            ConnDATA.sendto(bytes(sUdp, 'ascii'), (raddress, rport))
          try:
            buff, (raddress, rport) = ConnDATA.recvfrom(MAX_BLKSIZE)
            if python_version == 3:
              buff = buff.decode()
          except socket.error:
            print("[ERR]:[{}]:[{}] Error uploading file {}/{}".format(raddress, sReq, TFTP_FILES_PATH, nFile))
            break
          nBlock = int(hex_encode(buff[2:4]), 16)
          if ord(buff[1]) != 4 or nBlock != j:
            print("[ERR]:[{}]:[{}] Answer packet not valid: {}".format(raddress, sReq, ord(buff[1]), nBlock, j))
            break
          if len(data) < DEF_BLKSIZE:
            break
          data = f.read(DEF_BLKSIZE)
          fSize += len(data)
          if int(fSize / ECHO_FILE_SIZE) * ECHO_FILE_SIZE == fSize:
            print("[INFO]:[{}]:[{}] File {}/{} uploading success, size: {}".format(
              raddress, sReq, TFTP_FILES_PATH, nFile, fSize))
          if j == MAX_BLKCOUNT:
            j = 0
          else:
            j += 1
        f.close()
        ConnDATA.close()
        print("[INFO]:[{}]:[{}] File {}/{} finished uploading, size: {}".format(
          raddress, sReq, TFTP_FILES_PATH, nFile, fSize))
        sys.exit(0)
      sys.exit(0)


TftpServer('', TFTP_SOCK_TIMEOUT)
