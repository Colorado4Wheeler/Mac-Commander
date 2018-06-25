#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""plugin.py: Mac Commander plugin."""

__version__ 	= "2.0.0-b1"

__modname__		= "Mac Commander"
__author__ 		= "ColoradoFourWheeler"
__copyright__ 	= "Copyright 2018, ColoradoFourWheeler & EPS"
__credits__ 	= ["ColoradoFourWheeler"]
__license__ 	= "GPL"
__maintainer__ 	= "ColoradoFourWheeler"
__email__ 		= "Indigo Forums"
__status__ 		= "Production"

# Python Modules
import os
import sys
import time
import datetime
from subprocess import Popen, PIPE
import applescript
import glob
import re

# Third Party Modules
import indigo


class Plugin(indigo.PluginBase):

################################################################################
# INDIGO METHODS
################################################################################

	CONFIGDIR = ""  # Initialized in startup
	
	###
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.debug = False
		self.pollinglist = {}
		self.auditpolling = 0
		self.itunespollinglist = {} # 1.1.0
		
	###
	def __del__(self):
		indigo.PluginBase.__del__(self)
		
	###
	def startup(self):
		self.logger.debug (u"Starting Mac Commander")
		
		self.CONFIGDIR = '{}/Preferences/Plugins/{}'.format(indigo.server.getInstallFolderPath(), self.pluginId)
			
		if not os.path.exists (self.CONFIGDIR):
			os.makedirs (self.CONFIGDIR)
			self.logger.info (u"AppleScript script path set to {}".format(self.CONFIGDIR))
		
		# Run through all our devices and set up polling
		for dev in indigo.devices:
			if dev.pluginId == "com.eps.indigoplugin.mac-commander":
				self.configurePolling (dev, dev.ownerProps)
				self.configurePollingMusic (dev, dev.ownerProps) #1.1.0
	
	###
	def shutdown(self):
		self.debugLog(u"Mac Commander Shut Down")

	###
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
			
			
################################################################################
# INDIGO DEVICE METHODS
################################################################################
			
	###
	def validateDeviceConfigUi (self, valuesDict, typeId, devId):
		errorDict = indigo.Dict()
		dev = indigo.devices[devId]
		
		# While we are here add this device to polling if that is enabled
		self.configurePolling (dev, valuesDict)
		self.configurePollingMusic (dev, valuesDict)
		#indigo.server.log(unicode(self.itunespollinglist))
		
		return (True, valuesDict, errorDict)	
		
	###
	def actionControlDevice(self, action, dev):
		if dev.deviceTypeId == 'maccmd':
			if action.deviceAction == indigo.kDimmerRelayAction.TurnOn:
				self.command_turn_on(dev)
				
			elif action.deviceAction == indigo.kDimmerRelayAction.TurnOff:
				self.command_turn_off(dev)	
				
			elif action.deviceAction == indigo.kDimmerRelayAction.Toggle:
				if dev.onState:
					self.command_turn_off(dev)	
				else:
					self.command_turn_on(dev)
		

################################################################################
# INDIGO ACTION METHODS
################################################################################
		
	###
	def validateActionConfigUi(self, valuesDict, typeId, deviceId):
		"""
		Validate action form.
		"""
		
		errorsDict = indigo.Dict()
		
		if unicode(typeId) == 'runScript':
			if re.match('^[\w-]+$', valuesDict["name"]) is None:
				errorsDict["showAlertText"] = "Variable names must contain only alphanumeric letters or underscores."
				errorsDict["name"] = "Invalid character(s)"
				return (False, valuesDict, errorsDict)
			
		return (True, valuesDict, errorsDict)		
		
################################################################################
# MAC COMMAND RELAY DEVICE
################################################################################	
	###
	def command_turn_on (self, dev, props = {}):
		if not props: props = dev.pluginProps
	
		if props["onCommand"] == "none":
			return
		elif props["onCommand"] == "runapp":
			self.openApp (dev, "on", props)
			if not dev is None: 
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, props)
		elif props["onCommand"] == "quitapp":
			self.quitApp (dev, "on", props)
			if not dev is None: 
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, props)
		elif props["onCommand"] == "sleep":
			self.sleepComputer (dev, "on", props)
			if not dev is None: 
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, props)
		elif props["onCommand"] == "restart":
			self.restart_computer (dev, "on", props)
			if not dev is None: 
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, props)	
		elif props["onCommand"] == "screensaver":
			self.screenSaver (dev, "on", props)
			if not dev is None: 
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, props)
		elif props["onCommand"] == "showmessage":
			self.send_message (dev, "on", props)
		elif props["onCommand"] == "builtin":
			if props["onStandard"] == "playpause":
				self.playPause (dev, "on", props)
			if props["onStandard"] == "playlist":
				self.playList (dev, "on", props)
			if props["onStandard"] == "startitunes":
				self.startStopiTunes (dev, "start", props)
			if props["onStandard"] == "stopitunes":
				self.startStopiTunes (dev, "stop", props)
			
			# Since this was an ON command, turn it on
			if not dev is None:
				dev.updateStateOnServer("onOffState", True)
				self.configurePolling (dev, props)
		
	###
	def command_turn_off (self, dev):
		if dev.ownerProps["offCommand"] == "none":
			return
		elif dev.ownerProps["offCommand"] == "runapp":
			self.openApp (dev, "off")
			dev.updateStateOnServer("onOffState", False)
			self.configurePolling (dev, dev.ownerProps)
		elif dev.ownerProps["offCommand"] == "quitapp":
			self.quitApp (dev, "off")
			dev.updateStateOnServer("onOffState", False)
			self.configurePolling (dev, dev.ownerProps)
		elif dev.ownerProps["offCommand"] == "sleep":
			self.sleepComputer (dev, "off")
			dev.updateStateOnServer("onOffState", False)
			self.configurePolling (dev, dev.ownerProps)
		elif dev.ownerProps["onCommand"] == "restart":
			self.restart_computer (dev, "off")
			dev.updateStateOnServer("onOffState", False)
			self.configurePolling (dev, dev.ownerProps)	
		elif dev.ownerProps["offCommand"] == "screensaver":
			self.screenSaver (dev, "off")
			dev.updateStateOnServer("onOffState", False)
			self.configurePolling (dev, dev.ownerProps)
		elif dev.ownerProps["offCommand"] == "showmessage":
			self.send_message (dev, "off")	
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
		
################################################################################
# APPLESCRIPT HANDLER MIGRATED METHODS
################################################################################				

	###
	def run_applescript (self, action):
		"""
		Run an AppleScript from Actions.
		"""
		
		if not os.path.exists (u"{}/{}.scpt".format(self.CONFIGDIR, action.props['script'])):
			self.logger.error(u"Action to run AppleScript '{}' failed because that script does not exist in the folder".format(action.props['script']))
			return None
		
		self.logger.info (u"Running AppleScript '{}'".format(action.props['script']))
		script = applescript.AppleScript(path=u"{}/{}.scpt".format(self.CONFIGDIR, action.props['script']))
		response = script.run()
		
		if "extra" in action.props and action.props["extra"]:
			try:
				if action.props["extraAction"] == "storeNewVariable": 
					self.store_to_variable (action.props["name"], response)
				elif action.props["extraAction"] == "storeExistingVariable": 
					self.store_to_variable (action.props["variable"], response)
				elif action.props["extraAction"] == "storePlugin": 
					self.store_to_plugin (action.props["name"], response)
			except:
				pass
		
		return response
		
	###
	def get_stored_value (self, action):
		"""
		Hidden action return a stored value, must specify 'variable' in props.
		"""
		
		if not 'variable' in props:
			self.logger.error (u"Script attempted to retrieve a stored value but didn't pass a 'variable' property")
			return None
			
		if not u"saved_{}".format(props["variable"]) in self.pluginPrefs:
			self.logger.error (u"Script attempted to retrieve a stored value '{}' that value was never saved")
			return None		
			
		return self.pluginPrefs[u"saved_{}".format(props["variable"])]
		
	###
	def list_stored_variables (self):
		"""
		Read the pluginPrefs and output a list of all saved_* values.
		"""
		
		output = ""
		for key, value in self.pluginPrefs.iteritems():
			if key.startswith("saved_"): output += u"{}\n".format(key).replace("saved_", "")
			
		if output == "":
			self.logger.info("No variables have been saved to the plugin")
			return
			
		output = u"Values being saved in {}:\n{}".format(self.pluginDisplayName, output)
			
		self.logger.info(output)
		
	###
	def store_to_variable (self, variable, value):
		"""
		Store the value into a variable, creating it if needed.
		
		Arguments:
			variable:		name of the variable
			value:			value to unicode to the variable value
		"""
		
		if not variable in indigo.variables:
			try:
				indigo.variable.create(variable, u"{}".format(value))
			except:
				self.logger.error (u"Unable to create variable '{}', please check that it is a valid name, your AppleScript return value was not stored".format(variable))
		else:
			v = indigo.variables["MyVarName"]
			v.value = u"{}".format(value)
			v.replaceOnServer()
			self.logger.info(u"Variable '{}' has been updated from AppleScript".format(variable))
			
	###
	def store_to_plugin (self, variable, value):
		"""
		Store the actual value to the pluginPrefs with a prefix of 'saved_'.
		
		Arguments:
			variable:		name of the variable
			value:			value to unicode to the variable value
		"""
		
		try:
			self.pluginPrefs[u"saved_{}".format(variable)] = value
			self.logger.info(u"Plugin value '{}' has been updated from AppleScript".format(variable))
		except:
			self.logger.error (u"Unable to create variable '{}', please check that it is a valid name, your AppleScript return value was not stored".format(variable))
	
	###
	def get_folder_scripts (self, filter="", valuesDict=None, typeId="", targetId=0):
		"""
		Read preference folder for all scripts and return them as a list.
		"""
		
		try:
			retList = []
			
			scripts = glob.glob(self.CONFIGDIR + "/*.scpt")
			for script in scripts:
				scriptName = script.replace(self.CONFIGDIR + "/", "").replace(".scpt", "")
				retList.append ((scriptName, scriptName))
				
			return retList
			
		except Exception as e:
			self.logger.error(unicode(e))		
	
			
################################################################################
# LEGACY MAC COMMANDER ACTIONS
################################################################################		
	###
	def deviceAction (self, devAction):
		if devAction.deviceId: dev = indigo.devices[devAction.deviceId]
		action = devAction.pluginTypeId
		
		# First determine if we got a toggle so we can change the action
		if action == "toggle":
			if dev.onState:
				self.command_turn_off(dev)	
			else:
				self.command_turn_on(dev)
		
		if action == "turnOn":
			self.command_turn_on(dev)
		
		elif action == "turnOff":
			self.command_turn_off(dev)	
			
		elif action == 'notify':
			self.send_message (None, '', devAction.props)
			
		elif action == 'command':
			self.command_turn_on(None, devAction.props)
				
		else:
			return
	
	###
	def sleepComputer (self, dev, method, props = {}):
		cmd = " -e 'sleep'"
		cmd = self.encapsulateCmd (dev, cmd, "Finder", "Finder", props)
		result = self.runOsa (cmd)
		
		indigo.server.log(u"{}\n{}".format(cmd,result))
		
	###
	def restart_computer (self, dev, method, props = {}):
		cmd = " -e 'restart'"
		cmd = self.encapsulateCmd (dev, cmd, "Finder", "Finder", props)
		result = self.runOsa (cmd)	
		
	###
	def screenSaver (self, dev, method, props = {}):
		cmd = " -e 'open application file id \"com.apple.ScreenSaver.Engine\"'"
		cmd = self.encapsulateCmd (dev, cmd, "Finder", "Finder", props)
		result = self.runOsa (cmd)
		
	###
	def startStopiTunes (self, dev, method, props = {}):
		if method == "start":
			cmd = " -e 'set C to path to applications folder as string'"
			cmd += " -e 'open file (C & \"iTunes.app\")'"
		
			cmd = self.encapsulateCmd (dev, cmd, "Finder", "Finder", props)
		else:
			cmd = " -e 'quit'"
		
			cmd = self.encapsulateCmd (dev, cmd, "Finder", "iTunes", props)
			
		
		result = self.runOsa (cmd)
		
	###
	def playPause (self, dev, method, props = {}):
		cmd = " -e 'playpause'"
			
		cmd = self.encapsulateCmd (dev, cmd, "iTunes", "iTunes", props)	
		
		result = self.runOsa (cmd)
		
	###
	def playList (self, dev, method, props = {}):
		cmd = " -e 'play the playlist named \"" + dev.ownerProps[method + "Playlist"] + "\"'"
			
		cmd = self.encapsulateCmd (dev, cmd, "iTunes", "iTunes", props)	
		
		result = self.runOsa (cmd)
	
	###
	def quitApp (self, dev, method, props = {}):
		cmd = " -e 'quit'"
		cmd = self.encapsulateCmd (dev, cmd, "Finder", dev.ownerProps[method + "Appname"], props)
		
		result = self.runOsa (cmd)
		
	###
	def openApp (self, dev, method, props = {}):
		if not props: props = dev.pluginProps
		cmd = " -e 'set C to path to applications folder as string'"
		cmd += " -e 'open file (C & \"" + props[method + "Appname"] + ".app\")'"
		
		cmd = self.encapsulateCmd (dev, cmd, "Finder", "Finder", props)
		cmd += " -e 'return \"Hello World\"'"
		
		result = self.runOsa (cmd)
		
	###
	def send_message (self, dev, method, props = {}):
		if not props: props = dev.pluginProps
		cmd = " -e 'display notification \"{}\" with title \"Mac Commander for Indigo\"'".format(props[method + "Message"])
		cmd = self.encapsulateCmd (dev, cmd, "Finder", "Finder", props)
		
		result = self.runOsa (cmd)	
		
	###
	def encapsulateCmd (self, dev, cmd, terms, tell, props = {}):
		if not props: props = dev.pluginProps
		if props["localhost"] == True:
			return self.encapsulateIndigo (dev, cmd, terms, tell, props)
		else:
			return self.encapsulateRemote (dev, cmd, terms, tell, props)
			
	###
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
				
	###
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
		
	###
	def pollDevice (self, dev):
		if dev.ownerProps["pollmethod"] == "apprunning":
			self.pollingAppRunning (dev)
			
		if dev.ownerProps["itunespolling"]: #1.1.0
			self.pollingiTunesInfo (dev)
	
	###
	def encapsulateRemote (self, dev, cmd, terms, tell, props = {}):
		if not props: props = dev.pluginProps
		
		cmdex = "osascript "
		cmdex += " -e 'set R to \"eppc://" + props["username"] + ":" + props["password"] + "@" + props["computerip"] + "\"'"
		cmdex += " -e 'using terms from application \"" + terms + "\"'"
		cmdex += " -e 'tell application \"" + tell + "\" of machine R'"
		
		cmdex += cmd
		
		cmdex += " -e 'end tell'"
		cmdex += " -e 'end using terms from'"
	
		return cmdex
		
	###
	def encapsulateIndigo (self, dev, cmd, terms, tell, props = {}):
		if not props: props = dev.pluginProps
		
		cmdex = "osascript "
		cmdex += " -e 'using terms from application \"" + terms + "\"'"
		cmdex += " -e 'tell application \"" + tell + "\"'"
		
		cmdex += cmd
		
		cmdex += " -e 'end tell'"
		cmdex += " -e 'end using terms from'"
	
		return cmdex
		
	
			
	###
	def runOsa (self, cmd):
		result, tError = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()
		return result
		
	###
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
						
	###
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
		
	###
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
				
	###
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
				
		
		
	

	
