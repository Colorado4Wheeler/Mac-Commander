#! /usr/bin/env python
# -*- coding: utf-8 -*-

import indigo

import os
import sys
import time
import datetime
from subprocess import Popen, PIPE

################################################################################
class Plugin(indigo.PluginBase):
	
	#
	# Init
	#
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.debug = False
		self.pollinglist = {}
		self.auditpolling = 0
		self.itunespollinglist = {} # 1.1.0
		
	#
	# Delete
	#
	def __del__(self):
		indigo.PluginBase.__del__(self)
		
	#
	# Device action
	#
	def deviceAction (self, devAction):
		dev = indigo.devices[devAction.deviceId]
		action = devAction.pluginTypeId
		
		# First determine if we got a toggle so we can change the action
		if action == "toggle":
			if dev.states["onOffState"] == False:
				action = "turnOn"
			else:
				action = "turnOff"
		
		if action == "turnOn":
			if dev.ownerProps["onCommand"] == "none":
				return
			elif dev.ownerProps["onCommand"] == "runapp":
				self.openApp (dev, "on")
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, dev.ownerProps)
			elif dev.ownerProps["onCommand"] == "quitapp":
				self.quitApp (dev, "on")
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, dev.ownerProps)
			elif dev.ownerProps["onCommand"] == "sleep":
				self.sleepComputer (dev, "on")
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, dev.ownerProps)
			elif dev.ownerProps["onCommand"] == "screensaver":
				self.screenSaver (dev, "on")
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, dev.ownerProps)
			elif dev.ownerProps["onCommand"] == "builtin":
				if dev.ownerProps["onStandard"] == "playpause":
					self.playPause (dev, "on")
				if dev.ownerProps["onStandard"] == "playlist":
					self.playList (dev, "on")
				if dev.ownerProps["onStandard"] == "startitunes":
					self.startStopiTunes (dev, "start")
				if dev.ownerProps["onStandard"] == "stopitunes":
					self.startStopiTunes (dev, "stop")
					
				# Since this was an ON command, turn it on
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, dev.ownerProps)
		
		elif action == "turnOff":
			if dev.ownerProps["offCommand"] == "none":
				return
			elif dev.ownerProps["offCommand"] == "runapp":
				self.openApp (dev, "off")
				dev.updateStateOnServer("onOffState", False)
				self.configurePolling (dev, dev.ownerProps)
			elif dev.ownerProps["offCommand"] == "quitapp":
				self.quitApp (dev, "on")
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, dev.ownerProps)
			elif dev.ownerProps["offCommand"] == "sleep":
				self.sleepComputer (dev, "off")
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, dev.ownerProps)
			elif dev.ownerProps["offCommand"] == "screensaver":
				self.screenSaver (dev, "off")
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, dev.ownerProps)
			elif dev.ownerProps["offCommand"] == "builtin":
				if dev.ownerProps["offStandard"] == "playpause":
					self.playPause (dev, "off")
				if dev.ownerProps["offStandard"] == "playlist":
					self.playList (dev, "off")
				if dev.ownerProps["offStandard"] == "startitunes":
					self.startStopiTunes (dev, "start")
				if dev.ownerProps["offStandard"] == "stopitunes":
					self.startStopiTunes (dev, "stop")	
					
				# Since this was an OFF command, turn it off
				dev.updateStateOnServer("onOffState", False)
				self.configurePolling (dev, dev.ownerProps)
				
		else:
			return
	
	#
	# Put computer to sleep
	#
	def sleepComputer (self, dev, method):
		cmd = " -e 'sleep'"
		cmd = self.encapsulateCmd (dev, cmd, "Finder", "Finder")
		result = self.runOsa (cmd)
		
	#
	# Start screensaver
	#
	def screenSaver (self, dev, method):
		cmd = " -e 'open application file id \"com.apple.ScreenSaver.Engine\"'"
		cmd = self.encapsulateCmd (dev, cmd, "Finder", "Finder")
		result = self.runOsa (cmd)
		
	#
	# Start/stop iTunes
	#
	def startStopiTunes (self, dev, method):
		if method == "start":
			cmd = " -e 'set C to path to applications folder as string'"
			cmd += " -e 'open file (C & \"iTunes.app\")'"
		
			cmd = self.encapsulateCmd (dev, cmd, "Finder", "Finder")
		else:
			cmd = " -e 'quit'"
		
			cmd = self.encapsulateCmd (dev, cmd, "Finder", "iTunes")
			
		
		result = self.runOsa (cmd)
		
	#
	# Play/pause iTunes
	#
	def playPause (self, dev, method):
		cmd = " -e 'playpause'"
			
		cmd = self.encapsulateCmd (dev, cmd, "iTunes", "iTunes")	
		
		result = self.runOsa (cmd)
		
	#
	# Play iTunes playlist
	#
	def playList (self, dev, method):
		cmd = " -e 'play the playlist named \"" + dev.ownerProps[method + "Playlist"] + "\"'"
			
		cmd = self.encapsulateCmd (dev, cmd, "iTunes", "iTunes")	
		
		result = self.runOsa (cmd)
	
	#
	# Quit application
	#
	def quitApp (self, dev, method):
		cmd = " -e 'quit'"
		cmd = self.encapsulateCmd (dev, cmd, "Finder", dev.ownerProps[method + "Appname"])
		
	#
	# Open application
	# 
	def openApp (self, dev, method):
		cmd = " -e 'set C to path to applications folder as string'"
		cmd += " -e 'open file (C & \"" + dev.ownerProps[method + "Appname"] + ".app\")'"
		
		cmd = self.encapsulateCmd (dev, cmd, "Finder", "Finder")
		cmd += " -e 'return \"Hello World\"'"
		
		result = self.runOsa (cmd)
		
		
	
	# Encapsulate command
	def encapsulateCmd (self, dev, cmd, terms, tell):
		if dev.ownerProps["localhost"] == True:
			return self.encapsulateIndigo (dev, cmd, terms, tell)
		else:
			return self.encapsulateRemote (dev, cmd, terms, tell)
			
	#	
	# Polling: Application Running
	#
	def pollingAppRunning (self, dev):
		if dev.ownerProps["polling"]:
			cmd = " -e 'set X to (count every process whose name is \"" + dev.ownerProps["pollappname"] + "\")'"
			
			cmd = self.encapsulateCmd (dev, cmd, "Finder", "Finder")			
			cmd += " -e 'return X'"
			
			result = self.runOsa (cmd)
			#indigo.server.log(result)
			
			if result.startswith("0"):
				dev.updateStateOnServer("onOffState", False)
			else:
				dev.updateStateOnServer("onOffState", True)
				
	#	
	# Polling: iTunes info (1.1.0)
	#
	def pollingiTunesInfo (self, dev):
		indigo.server.log ("Getting itunes info")
		
		cmd = " -e 'set track_name to the name of the current track'"
		cmd += " -e 'set track_artist to the artist of the current track'"
		cmd += " -e 'set track_album to the album of the current track'"
		cmd = self.encapsulateCmd (dev, cmd, "iTunes", "iTunes")
		cmd += " -e 'return track_artist & \"|\" & track_album & \"|\" & track_name'"
		
		result = self.runOsa (cmd)
		result = result[:-1]
		
		playinfo = result.split("|")
		
		dev.updateStateOnServer("itunesartist", playinfo[0])
		dev.updateStateOnServer("itunesalbum", playinfo[1])
		dev.updateStateOnServer("itunessongname", playinfo[2])
		
	#
	# Poll the device
	#
	def pollDevice (self, dev):
		if dev.ownerProps["pollmethod"] == "apprunning":
			self.pollingAppRunning (dev)
			
		if dev.ownerProps["itunespolling"]: #1.1.0
			self.pollingiTunesInfo (dev)
	
	#
	# Encapsulate remote server into command
	#
	def encapsulateRemote (self, dev, cmd, terms, tell):
		cmdex = "osascript "
		cmdex += " -e 'set R to \"eppc://" + dev.ownerProps["username"] + ":" + dev.ownerProps["password"] + "@" + dev.ownerProps["computerip"] + "\"'"
		cmdex += " -e 'using terms from application \"" + terms + "\"'"
		cmdex += " -e 'tell application \"" + tell + "\" of machine R'"
		
		cmdex += cmd
		
		cmdex += " -e 'end tell'"
		cmdex += " -e 'end using terms from'"
	
		return cmdex
		
	#
	# Encapsulate local server into command
	#
	def encapsulateIndigo (self, dev, cmd, terms, tell):
		cmdex = "osascript "
		cmdex += " -e 'using terms from application \"" + terms + "\"'"
		cmdex += " -e 'tell application \"" + tell + "\"'"
		
		cmdex += cmd
		
		cmdex += " -e 'end tell'"
		cmdex += " -e 'end using terms from'"
	
		return cmdex
		
	
			
	# Run command
	def runOsa (self, cmd):
		result, tError = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()
		return result
		
	#
	# Set up device polling
	#
	def configurePolling (self, dev, settings):
		if str(dev.id) in self.pollinglist:
		
			# If polling disabled remove it from the list
			if settings["polling"] == False:
				self.pollinglist.pop(str(dev.id), None)
				return
				
			# If polling is on and its off remove it from the list
			if settings["polltype"] == "whenon":
				if dev.states["onOffState"] == False:
					self.pollinglist.pop(str(dev.id), None)
					return
					
			# If polling is off and its on remove it from the list
			if settings["polltype"] == "whenoff":
				if dev.states["onOffState"]:
					self.pollinglist.pop(str(dev.id), None)
					return
		
		else:
			if settings["polling"]:
			
				# Polling is for always, add it
				if settings["polltype"] == "always":
					self.pollinglist[str(dev.id)] = int(settings["pollfrequency"])
					return
					
				# Polling is on and the device is on, add it
				if settings["polltype"] == "whenon":
					if dev.states["onOffState"]:
						self.pollinglist[str(dev.id)] = int(settings["pollfrequency"])
						return
						
				# Polling is on and the device is on, add it
				if settings["polltype"] == "whenoff":
					if dev.states["onOffState"] == False:
						self.pollinglist[str(dev.id)] = int(settings["pollfrequency"])
						return
	#
	# Set up device polling for iTunes (1.1.0)
	#
	def configurePollingMusic (self, dev, settings):
		if str(dev.id) in self.itunespollinglist:
			# If polling disabled remove it from the list
			if settings["itunespolling"] == False:
				self.itunespollinglist.pop(str(dev.id), None)
				return
				
		else:
			if settings["itunespolling"]:
				self.itunespollinglist[str(dev.id)] = int(settings["itunespollfrequency"])
				return
		
	#
	# Tick down polling
	#
	def pollingTick (self):
		removelist = {}
		
		for devId, countdown in self.pollinglist.iteritems():
			countdown = countdown - 1
			if countdown == 0:
				# Execute the polling
				dev = indigo.devices[int(devId)]
				self.pollDevice (dev)
				
				# Always remove polling when 0 because we'll add it again later
				removelist[devId] = devId
				
			# Write the new countdown to the dict
			self.pollinglist[devId] = countdown
		
		# Run through the remove list and remove the device then check if it needs added again
			for devId in removelist:
				dev = indigo.devices[int(devId)]
				self.pollinglist.pop(str(dev.id), None)
				self.configurePolling (dev, dev.ownerProps)
				
	#
	# Tick down iTunes polling (1.1.0)
	#
	def pollingTickMusic (self):
		removelist = {}
		
		for devId, countdown in self.itunespollinglist.iteritems():
			countdown = countdown - 1
			if countdown == 0:
				# Execute the polling
				dev = indigo.devices[int(devId)]
				self.pollDevice (dev)
				
				# Always remove polling when 0 because we'll add it again later
				removelist[devId] = devId
				
			# Write the new countdown to the dict
			self.itunespollinglist[devId] = countdown
			
		# Run through the remove list and remove the device then check if it needs added again
			for devId in removelist:
				dev = indigo.devices[int(devId)]
				self.itunespollinglist.pop(str(dev.id), None)
				self.configurePollingMusic (dev, dev.ownerProps)
				
		
	#
	# Device configuration dialog closing
	#
	def validateDeviceConfigUi (self, valuesDict, typeId, devId):
		errorDict = indigo.Dict()
		dev = indigo.devices[devId]
		
		# While we are here add this device to polling if that is enabled
		self.configurePolling (dev, valuesDict)
		self.configurePollingMusic (dev, valuesDict)
		#indigo.server.log(unicode(self.itunespollinglist))
		
		return (True, valuesDict, errorDict)		
	
	#
	# Plugin startup
	#
	def startup(self):
		self.debugLog(u"Starting Mac Commander")
		
		# Run through all our devices and set up polling
		for dev in indigo.devices:
			if dev.pluginId == "com.eps.indigoplugin.mac-commander":
				self.configurePolling (dev, dev.ownerProps)
				self.configurePollingMusic (dev, dev.ownerProps) #1.1.0
	
	#	
	# Plugin shutdown
	#
	def shutdown(self):
		self.debugLog(u"Mac Commander Shut Down")


	#
	# Threading
	#
	def runConcurrentThread(self):
		try:
			while True:
					# Since we sleep for 1 second we can use this as crude 1 second timer
					if len(self.pollinglist) > 0:
						self.pollingTick()
						self.pollingTickMusic()
			
					self.sleep(1)
		except self.StopThread:
			pass	# Optionally catch the StopThread exception and do any needed cleanup.

	
