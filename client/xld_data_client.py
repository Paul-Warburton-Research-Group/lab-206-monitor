#!/usr/bin/python3 -uE
import socket as s
import struct
import sys
unit_test = False

# Available query commands and corresponding codes
CMD_DICT = \
{\
  "TEMP_MXC":		0x0000000000000001,\
  "TEMP_STILL":		0x0000000000000002,\
  "TEMP_4K":		0x0000000000000003,\
  "TEMP_50K":		0x0000000000000004,\
  #"RES_MXC":		0x0000000000000010,\
  #"RES_STILL":		0x0000000000000020,\
  #"RES_4K":		0x0000000000000030,\
  #"RES_50K":		0x0000000000000040,\
  "P1":	        	0x0000000000010000,\
  "P2": 		0x0000000000020000,\
  "P3":	        	0x0000000000030000,\
  "P4":	        	0x0000000000040000,\
  "P5":	        	0x0000000000050000,\
  "P6":	        	0x0000000000060000\
}

# Expected response length (in bytes) for any query
SEND_LEN = 8 # 64 bit values
RECV_LEN = 4 # 32 bit floats

# Server address
#ADDR = 'localhost' # For local testing
ADDR = '169.254.135.146'
PORT = 22127
TIMEOUT = 10.0 # s

# Socket class
class XLDClient:
    def __init__(self,server_addr,server_port):
        self.addr = server_addr
        self.port = server_port
        self.error_state = False
    
    # Send function
    def send_data(self,cmd):
        totalsent = 0
        while totalsent < SEND_LEN:
            sent = self.sock.send(cmd[totalsent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            totalsent = totalsent + sent
    
    # Receive function
    def recv_data(self):
        chunks = []
        bytes_recd = 0
        while bytes_recd < RECV_LEN:
            chunk = self.sock.recv(min(RECV_LEN - bytes_recd, 1024))
            if chunk == b'':
                raise RuntimeError("Socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)
    
    # Query function
    def query(self,query_cmd):
        
        # Error checking
        if query_cmd not in CMD_DICT.keys():
            print ("[ERROR]: query(): Unrecognized command '%s'." % query_cmd)
            return None
        
        # Get the command
        cmd = CMD_DICT[query_cmd]
        
        # Convert int to bytes
        cmd_bytes = cmd.to_bytes(SEND_LEN,sys.byteorder)
        #cmd_bytes = bytearray(struct.pack("Q",cmd))
        
        # Connect to the server
        try:
            self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)
            self.sock.connect((self.addr, self.port))
            
            # Send the query
            self.send_data(cmd_bytes)
            
            # Receive the response
            ret = self.recv_data()
            
            # Close
            self.sock.close()
            
            # Structure the response into float
            return float(struct.unpack("f",ret)[0])
        except Exception as e:
            print ("[ERROR]: query(): Exception %s" % repr(e.args))
            return 0.0

if unit_test:
    # Send queries
    client = XLDClient(ADDR,PORT)
    keys = list(CMD_DICT.keys())
    for key in keys:
        val = client.query(key)
        print ("[%s]: %e" % (key,val))

