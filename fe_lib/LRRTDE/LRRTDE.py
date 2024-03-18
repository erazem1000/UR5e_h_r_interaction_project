
import socket
import time
import threading
import struct
import sys
from collections import deque


class LRRTDE():
    def __init__(self):
        pass

    def connect(this, robot_ip, robot_port, protocol_ver):
        print("Creating TCP session...", end="")
        this.robot_ip = robot_ip
        this.robot_port = robot_port
        this.protocol_ver = protocol_ver
        try:
            this.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            this.sock.connect((this.robot_ip, this.robot_port))
        except Exception as e:
            print("Socket error.")
            print(e)
            return
        print("Done.")
        print("Negotiating RTDE protocol version...", end="")
        packet = struct.pack(">HcH", 5, b'V', 2)
        this.sock.sendall(packet)
        ret_packet = this.sock.recv(1024)
        ret_packet_obj = struct.unpack(">Hc?", ret_packet)
        this.sendBuf = deque(maxlen=100)
        this.oldBuf = b''

        if ret_packet_obj[2] == True:
            print("Done. Selected RTDEv%d." % this.protocol_ver)
            print("Checking controller firmware version...",end="")
            packet = struct.pack(">Hc", 3, b'v')
            this.sock.sendall(packet)
            ret_packet = this.sock.recv(1024)
            ret_packet_obj = struct.unpack(">HcIIII", ret_packet)
            print(ret_packet_obj[2:])
            return

        else:
            print("Error. Robot controller declined RTDEv%d" % this.protocol_ver)
            return

    def setOutputs(this, outputList, frequency):
        this.frequency = frequency
        this.outputList = outputList
        strOutputList = ",".join(outputList)
        print("Setting RTDE controller outputs as [%s]@%fHz." % (strOutputList, this.frequency))
        baOutputList = strOutputList.encode('ASCII')
        packet = struct.pack(">Hcd", len(baOutputList)+11, b'O', this.frequency)
        packet += baOutputList
        this.sock.sendall(packet)
        packet_ret = this.sock.recv(1024)
        this.outputTypes = packet_ret[4:].decode('ASCII').split(',')
        print("Receiving [%s] with a total length of %d." % (packet_ret[4:].decode('ASCII'), this.getTotalOutputLength()))

    def getTotalOutputLength(this):
        length = 0
        for t in this.outputTypes:
            if t == 'BOOL':
                length = length + 1
            elif t == 'UINT8':
                length = length + 1
            elif t == 'UINT32':
                length = length + 4
            elif t == 'UINT64':
                length = length + 8
            elif t == 'INT32':
                length = length + 4
            elif t == 'DOUBLE':
                length = length + 8
            elif t == 'VECTOR3D':
                length = length + 24
            elif t == 'VECTOR6D':
                length = length + 48
            elif t == 'VECTOR6INT32':
                length = length + 24
            elif t == 'VECTOR6UINT32':
                length = length + 24
        return length

    def start(this, fw_ip, fw_port):
        this.fw_ip = fw_ip
        this.fw_port = fw_port
        for t in this.outputTypes:
            if t == 'NOT_FOUND':
                print("Error. Wrong data field in output setting %s." % this.outputList[this.outputTypes.index(t)])
                sys.exit(-1)
        this.worker = threading.Thread(target=this.workerFun)
        this.worker.start()
        this.worker2 = threading.Thread(target=this.workerFun2)
        this.worker2.start()
        print("Started RTDE echo server from TCP@%s:%d to UDP@%s:%d." % (this.robot_ip, this.robot_port, this.fw_ip, this.fw_port))


    def stop(this):
        this.workerRunning = False
        this.worker.join()
        this.worker2Running = False
        #this.worker2.join()
        time.sleep(0.5)
        packet = struct.pack(">Hc", 3, b'P')
        this.sock.sendall(packet)
        try:
            this.sock.recv(1024)
        except:
            pass
        print("Stopped RTDE echo server.")

    
    def workerFun(this):
        packet = struct.pack(">Hc", 3, b'S')
        this.sock.sendall(packet)
        packet_ret = this.sock.recv(1024)
        #s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        this.workerRunning = True
        while(this.workerRunning):
            packet_ret = this.sock.recv(2048)
            packet_ret = this.oldBuf + packet_ret
            while(True):
                packet_len = struct.unpack(">H", packet_ret[0:2])[0]
                this.sendBuf.append(packet_ret[0:packet_len])
               # print(struct.unpack(">d", packet_ret[4:12])[0])
                packet_ret = packet_ret[packet_len:]
                
                if(len(packet_ret) < (this.getTotalOutputLength() + 4)):
                    #print(len(packet_ret))
                    this.oldBuf = packet_ret
                    break

    def workerFun2(this):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        this.worker2Running = True
        while(this.worker2Running):
            #print("Send buf: ",len(this.sendBuf))
            if(len(this.sendBuf)):
                #print("sending")
                a = this.sendBuf.popleft()
                #a[4:]
                s.sendto(a[4:], (this.fw_ip, this.fw_port))
            

