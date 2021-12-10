import wx
import sys
import ast
import time
import numpy as np
import collections as c
import configparser as cp
import matplotlib as mpl
import matplotlib.dates as mpld
from matplotlib.backends.backend_wxagg import (
	FigureCanvasWxAgg as FigureCanvas,
	NavigationToolbar2WxAgg as NavigationToolbar)
import triton_data_client as xdc
import arduino_client as adc

CMD_LIST1 = [
	"PT1 Head T(K)",
	"PT1 Plate T(K)",
	"PT2 Head T(K)",
	"PT2 Plate T(K)",
	"Still Plate T(K)",
	"Cold Plate T(K)",
	"MC Plate Cernox T(K)",
	"MC Plate RuO2 T(K)",
	"Channel 9 T(K)"
]

CMD_LIST2 = [
	"P1 Tank (Bar)",
	"P2 Condense (Bar)",
	"P3 Still (mBar)",
	"P4 TurboBack (mBar)",
	"P5 ForepumpBack (Bar)",
	"Dewar (mBar)"
]

CMD_LIST3 = [
	"Input Water Temp",
	"Output Water Temp",
	"Oil Temp",
	"Helium Temp",
	"CDA Temp (C)",
	"Trap Temp"
]

CMD_LIST4 = [
	"Low Pressure",
	"High Pressure",
	"CDA Pressure (Bar)"
]

NON_TRITON_COMMANDS = adc.CMDS

def OnFrameExit(event):
	src = event.GetEventObject()
	
	# Check we really want to quit
	dial = wx.MessageDialog(None, 'Proceed?', 'Exit', wx.YES_NO | wx.NO_DEFAULT)
	ret = dial.ShowModal()
	if ret == wx.ID_NO:
		return
	
	# Dump the data to a file??
	
	print("Quitting.")
	sys.exit(0)

def add_rem_event(event):
	src = event.GetEventObject().GetParent()
	sel = src.box.GetSelection()
	if sel == -1:
		return
	else:
		choice = src.choices[sel]
		if choice not in src.active:
			src.active.append(choice)
		else:
			src.active.remove(choice)

class Plot(wx.Panel):
	def __init__(self, parent, choices, default_choices, id=-1, dpi=None, **kwargs):
		super().__init__(parent, id=id, **kwargs)
		self.figure = mpl.figure.Figure(dpi=dpi, figsize=(10, 6), constrained_layout=True)
		self.canvas = FigureCanvas(self, -1, self.figure)
		self.toolbar = NavigationToolbar(self.canvas)
		self.toolbar.Realize()
		
		self.choices = choices
		self.active = default_choices
		self.box = wx.ComboBox(self, choices=choices, style=wx.CB_READONLY, size=wx.Size(400,20))
		font = self.box.GetFont()
		font.SetPointSize(12)
		self.box.SetFont(font)
		
		self.add = wx.Button(self, label="Add/Rem", size=wx.Size(80,20), id=id)
		font = self.add.GetFont()
		font.SetPointSize(12)
		self.add.SetFont(font)
		self.add.Bind(wx.EVT_BUTTON, add_rem_event)
		
		bsizer = wx.BoxSizer(wx.HORIZONTAL)
		bsizer.Add(self.toolbar, 1, wx.LEFT | wx.EXPAND)
		bsizer.Add(self.box, 0, wx.RIGHT | wx.CENTRE | wx.EXPAND)
		bsizer.Add(self.add, 0, wx.RIGHT | wx.CENTRE | wx.EXPAND)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.canvas, 1, wx.EXPAND)
		sizer.Add(bsizer, 0, wx.EXPAND)
		self.SetSizer(sizer)


class MainFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, title="Triton Monitor GUI", style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
		
		# Load configuration
		self.loadConfig('config.cfg')
		
		# Load the queues
		self.initQueues()
		
		# Client instance
		self.triton_mon = xdc.XLDClient(self.config['GENERAL']['triton_addr'], int(self.config['GENERAL']['triton_port']))
		self.arduino = adc.ArduinoClient(self.config['GENERAL']['arduino_com'], int(self.config['GENERAL']['arduino_baud']))
		
		# Create a panel and notebook (tabs holder)
		p = wx.Panel(self)
		nb = wx.Notebook(p)
		
		# Create plots
		self.page1 = Plot(nb, CMD_LIST1, ast.literal_eval(self.config['DR_TEMP']['default']), id=100)
		nb.AddPage(self.page1, "DR Temperatures")
		
		self.page2 = Plot(nb, CMD_LIST2, ast.literal_eval(self.config['DR_PRES']['default']), id=200)
		nb.AddPage(self.page2, "DR Pressures")
		
		self.page3 = Plot(nb, CMD_LIST3, ast.literal_eval(self.config['SV_TEMP']['default']), id=300)
		nb.AddPage(self.page3, "Services Temperatures")
		
		self.page4 = Plot(nb, CMD_LIST4, ast.literal_eval(self.config['SV_PRES']['default']), id=400)
		nb.AddPage(self.page4, "Services Pressures")
		
		# Set notebook in a sizer to create the layout
		sizer = wx.BoxSizer()
		sizer.Add(nb, 1, wx.EXPAND)
		p.SetSizer(sizer)
		p.GetSizer().Fit(self)
		
		# Set a timer to update figures periodically
		self.timer = wx.Timer(self, -1)
		self.Bind(wx.EVT_TIMER, updatePlots)
		self.timer.Start(int(1000*self.delay))
	
	def initQueues(self):
		self.delay = float(self.config['GENERAL']['delay'])
		time_window = float(self.config['GENERAL']['window'])
		queue_size = int(time_window/self.delay)
		self.queue_x = c.deque(maxlen=queue_size)
		
		# FIG 1
		self.queues1 = {}
		for k in CMD_LIST1:
			self.queues1[k] = c.deque(maxlen=queue_size)
		
		# FIG 2
		self.queues2 = {}
		for k in CMD_LIST2:
			self.queues2[k] = c.deque(maxlen=queue_size)
		
		# FIG 3
		self.queues3 = {}
		for k in CMD_LIST3:
			self.queues3[k] = c.deque(maxlen=queue_size)
		
		# FIG 4
		self.queues4 = {}
		for k in CMD_LIST4:
			self.queues4[k] = c.deque(maxlen=queue_size)
	
	def updateQueues(self):
		self.queue_x.append(time.time())
		ext = self.arduino.read()
		
		# FIG 1
		for i, k in enumerate(CMD_LIST1):
			self.queues1[k].append(self.triton_mon.query(k))
		
		# FIG 2
		for i, k in enumerate(CMD_LIST2):
			self.queues2[k].append(self.triton_mon.query(k))
		
		# FIG 3
		for i, k in enumerate(CMD_LIST3):
			if k in NON_TRITON_COMMANDS:
				self.queues3[k].append(ext[k])
				continue
			self.queues3[k].append(self.triton_mon.query(k))
		
		# FIG 4
		for i, k in enumerate(CMD_LIST4):
			if k in NON_TRITON_COMMANDS:
				self.queues4[k].append(ext[k])
				continue
			self.queues4[k].append(self.triton_mon.query(k))
	
	def loadConfig(self, file):
		self.config = cp.ConfigParser(interpolation=cp.ExtendedInterpolation())
		fd = open(file, 'r')
		lines = fd.read().split("\n")
		fd.close()
		self.config.read_file(lines)
	
def updatePlots(event):
	event.GetEventObject().updateQueues()
	xdata = np.array(list(event.GetEventObject().queue_x))
	
	# FIG 1
	ydata = {k:np.array(list(x)) for k, x in event.GetEventObject().queues1.items()}
	fig = event.GetEventObject().page1.figure
	canvas = event.GetEventObject().page1.canvas
	active = event.GetEventObject().page1.active
	fig.clf()
	ax = fig.gca()
	for i, k in enumerate(active):
		ax.plot_date(mpld.epoch2num(xdata), ydata[k], "C%i-"%i, xdate=True, label=active[i])
	ax.set_xlabel("Date")
	ax.set_ylabel("Temperature (K)")
	ax.set_yscale("log")
	ax.legend(loc=2)
	canvas.draw()
	
	# FIG 2
	ydata = {k:np.array(list(x)) for k, x in event.GetEventObject().queues2.items()}
	fig = event.GetEventObject().page2.figure
	canvas = event.GetEventObject().page2.canvas
	active = event.GetEventObject().page2.active
	fig.clf()
	ax = fig.gca()
	for i, k in enumerate(active):
		ax.plot_date(mpld.epoch2num(xdata), ydata[k], "C%i-"%i, xdate=True, label=active[i])
	ax.set_xlabel("Date")
	ax.set_ylabel("Pressure (Bar or mBar)")
	ax.set_yscale("log")
	ax.legend(loc=2)
	canvas.draw()
	
	# FIG 3
	ydata = {k:np.array(list(x)) for k, x in event.GetEventObject().queues3.items()}
	fig = event.GetEventObject().page3.figure
	canvas = event.GetEventObject().page3.canvas
	active = event.GetEventObject().page3.active
	fig.clf()
	ax = fig.gca()
	for i, k in enumerate(active):
		ax.plot_date(mpld.epoch2num(xdata), ydata[k], "C%i-"%i, xdate=True, label=active[i])
	ax.set_xlabel("Date")
	ax.set_ylabel("Temperature (K)")
	ax.set_yscale("log")
	ax.legend(loc=2)
	canvas.draw()
	
	# FIG 4
	ydata = {k:np.array(list(x)) for k, x in event.GetEventObject().queues4.items()}
	fig = event.GetEventObject().page4.figure
	canvas = event.GetEventObject().page4.canvas
	active = event.GetEventObject().page4.active
	fig.clf()
	ax = fig.gca()
	for i, k in enumerate(active):
		ax.plot_date(mpld.epoch2num(xdata), ydata[k], "C%i-"%i, xdate=True, label=active[i])
	ax.set_xlabel("Date")
	ax.set_ylabel("Pressure (Bar)")
	ax.set_yscale("log")
	ax.legend(loc=2)
	canvas.draw()

def demo():
	app = wx.App()
	main = MainFrame()
	main.Bind(wx.EVT_CLOSE, OnFrameExit)
	main.Show()
	app.MainLoop()

if __name__ == "__main__":
	demo()