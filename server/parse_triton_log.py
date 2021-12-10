#
#    Triton Log Parsing
#
import sys
import os
import datetime
import time
import struct
unit_test = True

LOG_BASE = "C:\\Oxford Instruments\\LogFiles\\Warburton _68756\\"
col_indices = {}

def latest_logfile():
    # Get all VCL files in directory
    vcl_files = [LOG_BASE+f for f in os.listdir(LOG_BASE) if f.split('.')[-1] == 'vcl']
    
    # Compare access times
    # POTENTIAL BUGS HERE
    now = time.time()
    access_times = [os.stat(vclf).st_atime - now for vclf in vcl_files]
    latest_file = vcl_files[access_times.index(max(access_times))]
    
    return latest_file
        

def parse_vcl_info():
    # Get file header
    fd = open(latest_logfile(),"rb")
    header = fd.read(0x3000)
    fd.close()
    
    # Extract useful info
    metadata = header[0:0x400]
    comments = header[0x400:0x1800]
    colnames = header[0x1800:0x2f00]
    axissele = header[0x2f00:0x3000]
    
    # Only use col names and indices for now
    col_indices = {
        colnames[i*32:(i+1)*32].decode('utf-8').strip('\x00'):i\
        for i in range(184) if colnames[i*32:(i+1)*32].decode('utf-8').strip('\x00') != ''
    }
    
    return col_indices

def parse_vcl_last_line():
    
    # Get file size
    filename = latest_logfile()
    filesize_b = os.stat(filename).st_size
    fd = open(filename,"rb")
    
    # Check the size is greater than header
    if filesize_b <= 0x3000:
        print ("[WARN]: New logfile has no data yet.")
        return b'\x00'*8*len(col_indices) # Zeros
    
    # Data block, need to read only the last part of the file
    fd.seek(filesize_b - 8*len(col_indices))
    data = fd.read()
    fd.close()
    
    return data

def update_column_names_file():
    global col_indices
    if col_indices == {}: # This should never change in theory,
                          # as long as the Triton system is not changed.
        print("Updated column indices.")
        col_indices = parse_vcl_info()
    
    
    fd = open("column_names.txt",'w')
    fd.write("\n".join(["0x%.16X: \"%s\"," % (1 << i, k) for i, k in enumerate(col_indices.keys())]))
    
    fd.write("\n\n\n")
    
    fd.write("\n".join(["\"%s\": 0x%.16X," % (k, 1 << i) for i, k in enumerate(col_indices.keys())]))
    
    fd.close()

def getRowData():
    global col_indices
    if col_indices == {}: # This should never change in theory,
                          # as long as the Triton system is not changed.
        print("Updated column indices.")
        col_indices = parse_vcl_info()
    
    # Get the last row
    data = parse_vcl_last_line()
    
    ret = {}
    for key, index in col_indices.items():
        ret[key] = struct.unpack("d", data[index*8 : (index + 1)*8])[0]
    return ret

if unit_test:
    if 0:
        print("Latest logfile:")
        print(latest_logfile())
        print("")
        
        print("Column names and indices:")
        col_indices = parse_vcl_info()
        print(col_indices)
        print("")
        
        print("Last line of data:")
        data = parse_vcl_last_line()
        print(data)
        print("")
    
    # Test this by itself for self-updating mechanism
    print("Interpreted data:")
    idata = getRowData()
    print(idata)
    print("")
    
    update_column_names_file()
    