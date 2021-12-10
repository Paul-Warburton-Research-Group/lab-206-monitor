#
#    XLD Log Parsing
#
import sys
import os
import datetime
unit_test = False

# Mapping from data to channel numbers on the LSCI 372
T_MAP = \
{\
    "TEMP_MXC":		"CH6 T",\
    "TEMP_STILL":	"CH5 T",\
    "TEMP_4K":		"CH2 T",\
    "TEMP_50K":		"CH1 T",\
}

# Mapping from data to column numbers in the maxigauge logging file
P_MAP = \
{\
    "P1":           5,\
    "P2":           11,\
    "P3":           17,\
    "P4":           23,\
    "P5":           29,\
    "P6":           35\
}

# Temperature and pressure log base directories
XLD_TEMP_LOG_BASE = "C:\\Users\\Cryogenic Ltd\\Documents\\XLD Logging\\LSCI 372\\"
XLD_PRES_LOG_BASE = "C:\\Users\\Cryogenic Ltd\\Documents\\XLD Logging\\Valve Control\\"

# Parse temperature log file
def parseTempLog(cmd,filename):
    
    # Read all file contents in one go
    fd = open(filename,'r')
    full_str = fd.read()
    fd.close()
    
    # Get last line that isn't empty
    recent_line = (full_str.split("\n")[-2])
    
    # Get requested value
    return recent_line.split(",")[2]

# Parse pressure log file
def parsePresLog(cmd,filename):
    
    # Read all file contents in one go
    fd = open(filename,'r')
    full_str = fd.read()
    fd.close()
    
    # Get last line that isn't empty
    recent_line = (full_str.split("\n")[-2])
    
    # Get requested value
    return recent_line.split(",")[P_MAP[cmd]]

# Get required data
def getLogData(cmd):
    
    # Get the date now
    DATE = str(datetime.datetime.now().strftime("%y-%m-%d"))
    
    # Get day before in case log file does not exist yet
    DATEB4 = str((datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%y-%m-%d"))
    
    # Select between time and pressure
    if cmd in list(T_MAP.keys()):
    
        # Construct filename
        logfilename = XLD_TEMP_LOG_BASE + DATE + "\\" + T_MAP[cmd] + " %s.log" % (DATE)
        
        # Check file exists, if not use yesterday's file
        if not os.path.isfile(logfilename):
            logfilename = XLD_TEMP_LOG_BASE + DATEB4 + "\\" + T_MAP[cmd] + " %s.log" % (DATEB4)
        
        # Get the requested value
        return parseTempLog(cmd,logfilename)
        
    elif cmd in list(P_MAP.keys()):
        
        # Construct filename
        logfilename = XLD_PRES_LOG_BASE + DATE + "\\" + "maxigauge %s.log" % (DATE)
        
        # Check file exists, if not use yesterday's file
        if not os.path.isfile(logfilename):
            logfilename = XLD_PRES_LOG_BASE + DATEB4 + "\\" + "maxigauge %s.log" % (DATEB4)
        
        # Get the requested value
        return parsePresLog(cmd,logfilename)
        
    else:
        print ("[ERROR]: getLogData(): Invalid command '%s'." % cmd)
        return None

if unit_test:
    print ("Temperature values:")
    for key in list(T_MAP.keys()):
        print ("%s: %s" % (key,getLogData(key)))

    print ("\nPressure values:")
    for key in list(P_MAP.keys()):
        print ("%s: %s" % (key,getLogData(key)))