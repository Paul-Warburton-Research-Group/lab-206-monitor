import serial as s
import sys
import time
import numpy as np

CMDS = [
	"CDA Temp (C)",
	"CDA Pressure (Bar)",
	"Trap Temp"
]

class ArduinoClient:
	def __init__(self, port, baud):
		try:
			self.session = s.Serial(port, baud, timeout=1)
		except OSError as e:
			print (e)
			sys.exit(1)
		
		# Trap sensor parameters
		self.R0=1e3
		self.Rs = 2e3
		self.Vref = 1.1
		self.Vs = 3.3
		self.a=3.9083e-3
		self.b=-5.775e-7
		self.cp=-4.183e-12
		self.Tabs=-273.15
		self.Tarr1 = np.linspace(self.Tabs+1, -0.001, 5001)
		self.Tarr2 = np.linspace(0, 600, 5001)
	
	# Trap T Sensor functions
	def get_R(self, T):
		if T[0] < 0:
			return self.R0*(1+ self.a*T + self.b*T**2 + self.cp*(T-100)*T**3)
		else:
			return self.R0*(1+ self.a*T + self.b*T**2)
	
	def find_T(self, R):
		if R < 1000:
			index = np.argmin(np.abs(self.get_R(self.Tarr1)-R)**2)
			return self.Tarr1[index]
		else:
			index = np.argmin(np.abs(self.get_R(self.Tarr2)-R)**2)
			return self.Tarr2[index]
	
	def ADCout2Temp(self, count):
		Vt = count*self.Vref/(2**10)
		Rt = Vt*self.Rs/(self.Vs-Vt)
		return self.find_T(Rt) - self.Tabs
		
	# Readings
	def read(self):
		self.session.reset_input_buffer()
		data = self.session.read(8)
		
		status = int.from_bytes(data[0:2],'little',signed=False)
		if status == 3:
			print("Sensor reports an error.")
		pcount = int.from_bytes(data[2:4],'little',signed=False)
		cda_pr = (pcount-1000)*6.89476/14000
		tcount = int.from_bytes(data[4:6],'little',signed=False)
		cda_tmp = tcount*200/2048 - 50
		trcount = int.from_bytes(data[6:8],'little',signed=True)
		trap_tmp = self.ADCout2Temp(trcount)
		ret = {
			"CDA Temp (C)": cda_tmp,
			"CDA Pressure (Bar)": cda_pr,
			"Trap Temp": trap_tmp
		}
		return ret
	
	def close(self):
		self.session.close()












