import sys, os, socket

TFTP_FILES_PATH = 'tftp'  # path to files for transfering
TFTP_SERVER_PORT = 69
TFTP_GET_BYTE = 1
TFTP_PUT_BYTE = 2
TFTP_SOCK_TIMEOUT = 180 # in sec
TFTP_MIN_DATA_PORT = 44000  # range of UDP data port
TFTP_MAX_DATA_PORT = 65000  # -//-
DEF_BLKSIZE = 512  # size of data block in TFTP-packet
ECHO_FILE_SIZE = 0xa00000  # count of loaded or transfering bytes for print log message about this process (10 Mb)
MAX_BLKSIZE = 0x10000
MAX_BLKCOUNT = 0xffff


def TftpServer(sBindIp, SocketTimeout):
    print '-= DvK =- TFTP server 2017(p)'

    try:
        os.mkdir('tftp')
    except OSError:
        print('[INFO]: Directory already exists. OK.')

    print '[INFO]: binding socket ..',
    try:
        ConnUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ConnUDP.settimeout(SocketTimeout)
        ConnUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ConnUDP.bind((sBindIp, TFTP_SERVER_PORT))
    except socket.error as msg:
        print 'error: %s' % msg
        return
    print 'ok'

    dPort = TFTP_MIN_DATA_PORT
    while True:
        try:
            buff, (raddress, rport) = ConnUDP.recvfrom(MAX_BLKSIZE)
        except socket.timeout:
            pass
        except socket.error:
            return
        print '[INFO]: connect from ', raddress, rport
        sReq = ''
        tReq = ord(buff[1])
        if tReq == TFTP_GET_BYTE:
            sReq = 'get'
            fMode = 'r'
        if tReq == TFTP_PUT_BYTE:
            sReq = 'put'
            fMode = 'w'
        if len(sReq) == 0:
            print '[ERR]: illegal TFTP request', tReq
            sUdp = '\x00\x05\x00\x01Illegal TFTP request\x00'
            ConnUDP.sendto(sUdp, (raddress, rport))
            continue
        ss = buff[2:].split('\0')
        nFile = ss[0]
        sType = ss[1]
        print '[INFO]:[' + raddress + '] ' + sReq + 'ing file', nFile, sType
        if (sType == 'octet'):
            fMode += 'b'
        try:
            f = open(TFTP_FILES_PATH + '/' + nFile, fMode)
        except IOError:
            print '[INFO]:[' + raddress + ']:[' + sReq + '] error open file: ' + TFTP_FILES_PATH + '/' + nFile
            sUdp = '\x00\x05\x00\x01Error open file\x00'
            ConnUDP.sendto(sUdp, (raddress, rport))
            continue
        try:
            ConnDATA = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ConnDATA.settimeout(SocketTimeout)
            ConnDATA.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            ConnDATA.bind(('', dPort))
        except socket.error:
            print '[ERR]:[' + raddress + ']:[' + sReq + '] error binding dataport', dPort
            sUdp = '\x00\x05\x00\x01Internal error\x00'
            ConnUDP.sendto(sUdp, (raddress, rport))
            f.close()
            continue
        print '[INFO]:[' + raddress + ']:[' + sReq + '] success binding data port', dPort
        dPort += 1
        if dPort == TFTP_MAX_DATA_PORT:
            dPort = TFTP_MIN_DATA_PORT
        child_pid = os.fork()
        if child_pid < 0:
            print '[ERR]:[' + raddress + ']:[' + sReq + '] error forking new process'
            sUdp = '\x00\x05\x00\x01Internal error\x00'
            ConnUDP.sendto(sUdp, (raddress, rport))
            f.close()
            ConnDATA.close()
            continue
        if child_pid == 0:
            if sReq == 'put':
                sUdp = '0004' + ('%04x' % 0)
                ConnDATA.sendto(sUdp.decode('hex'), (raddress, rport))
                fSize = 0
                buffer, (raddress, rport) = ConnDATA.recvfrom(MAX_BLKSIZE)
                while buffer:
                    fSize += len(buffer[4:])
                    f.write(buffer[4:])
                    sUdp = '\x00\x04' + buffer[2:4]
                    ConnDATA.sendto(sUdp, (raddress, rport))
                    if len(buffer[4:]) < DEF_BLKSIZE:
                        break
                    buffer, (raddress, rport) = ConnDATA.recvfrom(MAX_BLKSIZE)
                    if int(fSize / ECHO_FILE_SIZE) * ECHO_FILE_SIZE == fSize:
                        print '[INFO]:[' + raddress + ']:[' + sReq + '] file ' + TFTP_FILES_PATH + '/' + nFile + ' downloading, size:', fSize
                f.close()
                ConnDATA.close()
                print '[INFO]:[' + raddress + ']:[' + sReq + '] file ' + TFTP_FILES_PATH + '/' + nFile + ' finish download, size:', fSize
                sys.exit(0)
            if sReq == 'get':
                data = f.read(DEF_BLKSIZE)
                fSize = len(data)
                j = 1
                while data:
                    sUdp = ('0003' + ('%04x' % j)).decode('hex') + data
                    ConnDATA.sendto(sUdp, (raddress, rport))
                    try:
                        buffer, (raddress, rport) = ConnDATA.recvfrom(MAX_BLKSIZE)
                    except socket.error:
                        print '[ERR]:[' + raddress + ']:[' + sReq + '] error upload file ' + TFTP_FILES_PATH + '/' + nFile
                        break
                    nBlock = int(buffer[2:4].encode('hex'), 16)
                    if ord(buffer[1]) != 4 or nBlock != j:
                        print '[ERR]:[' + raddress + ']:[' + sReq + '] answer packet not valid:', ord(
                            buffer[1]), nBlock, j
                        break
                    if len(data) < DEF_BLKSIZE:
                        break
                    data = f.read(DEF_BLKSIZE)
                    fSize += len(data)
                    if int(fSize / ECHO_FILE_SIZE) * ECHO_FILE_SIZE == fSize:
                        print '[INFO]:[' + raddress + ']:[' + sReq + '] file ' + TFTP_FILES_PATH + '/' + nFile + ' uploading success, size:', fSize
                    if j == MAX_BLKCOUNT:
                        j = 0
                    else:
                        j += 1
                f.close()
                ConnDATA.close()
                print '[INFO]:[' + raddress + ']:[' + sReq + '] file ' + TFTP_FILES_PATH + '/' + nFile + ' finish upload, size:', fSize
                sys.exit(0)
            sys.exit(0)


##########################################################################################

TftpServer('', TFTP_SOCK_TIMEOUT)
