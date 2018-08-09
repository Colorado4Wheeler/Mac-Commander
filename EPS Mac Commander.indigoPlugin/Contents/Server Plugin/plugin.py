#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""plugin.py: Mac Commander plugin."""

__version__ 	= "2.0.0"

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
from datetime import datetime, timedelta, time
import subprocess
from subprocess import Popen, PIPE
import applescript
import glob
import re
import base64
import thread
from xml.etree import cElementTree
#import psutil

# Third Party Modules
#sys.path.append('lib/psutil')
import indigo
from lib.pexpect import pxssh


# Package Modules
from lib.eps import ex
from lib.eps import version

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
		if not 'credentials' in self.pluginPrefs: self.pluginPrefs['credentials'] = []
		
		self.next_version_check = datetime.now() + timedelta(days=7)
		version.version_check(self)
				
		#indigo.server.log(u'{}'.format(psutil.cpu_percent()))
		
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
		for dev in indigo.devices.iter("self"):
			if dev.pluginId == "com.eps.indigoplugin.mac-commander" and (dev.deviceTypeId =='maccmd' or dev.deviceTypeId =='epsmc') :
				self.configurePolling (dev, dev.ownerProps)
				self.configurePollingMusic (dev, dev.ownerProps) #1.1.0
				
			elif dev.pluginId == "com.eps.indigoplugin.mac-commander" and dev.deviceTypeId =='computer':
				#thread.start_new_thread (self.sample_computer_data, (dev,))
				pass

	
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
					
				if self.next_version_check < datetime.now():
					version.version_check(self)
					
				for dev in indigo.devices.iter("self"):	
					if dev.deviceTypeId == 'computer' and dev.pluginProps['refresh'] != '0':
						last = datetime.strptime(dev.states['last_sample'], "%Y-%m-%d %H:%M:%S")
						next = last + timedelta(seconds=int(dev.pluginProps['refresh']))
						if datetime.now() > next: thread.start_new_thread (self.sample_computer_data, (dev,))
						
					
		except self.StopThread:
			pass	# Optionally catch the StopThread exception and do any needed cleanup.


	###
	def deviceStartComm (self, dev):
		dev.stateListOrDisplayStateIdChanged() # Commit any state changes

################################################################################
# COMPUTER
################################################################################			
	
	###
	def sample_computer_profile (self, dev):
		try:
			regex = re.compile(r'''
				[\S]+:                # a key (any word followed by a colon)
				(?:
				\s                    # then a space in between
					(?!\S+:)\S+       # then a value (any word not followed by a colon)
				)+                    # match multiple values if present
				''', re.VERBOSE)
				
			if dev.pluginProps['localhost']:
				cmd = [ '/usr/sbin/system_profiler', 'SPHardwareDataType', 'SPSoftwareDataType']
				profiler = subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0]
				hardwareraw = regex.findall(profiler)
				indigo.server.log(unicode(hardwareraw))
				
				#cmd = [ '/usr/sbin/system_profiler', 'SPSoftwareDataType']
				#profiler = subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0]
				#softwareraw = regex.findall(profiler)
				
			else:
				s = self.ssh (dev.pluginProps, "Sampling")
				if s:		
					s.sendline ('pwd')
					s.sendline ('echo "#! /usr/bin/env python" > test.py')
					s.sendline ('sudo /usr/sbin/system_profiler SPHardwareDataType SPSoftwareDataType')
					s.prompt(timeout=1)
					profiler = s.before
					
					hardwareraw = regex.findall(profiler)
					indigo.server.log(unicode(profiler))
					
					s.expect('[#\$] ')
					
					#s.sendline ('echo "#! /usr/bin/env python" > test.py')
					s.prompt(timeout=1)
			
			profile = {}
			
			for i in range(0, len(hardwareraw)):
				value = hardwareraw[i].split(": ")
				if i == 0: profile['Model Name'] = value[1]
				if i == 1: profile['Model ID'] = value[1]
				if i == 2: profile['CPU'] = value[1]
				if i == 3: profile['CPU Speed'] = value[1]
				if i == 4: profile['Processors'] = int(value[1])
				if i == 5: profile['Cores'] = int(value[1])
				if i == 8: profile['Memory'] = value[1]
				if i == 11: profile['Serial Number'] = value[1]
				if i == 13: profile['macOS Version'] = value[1]
				if i == 14: profile['macOS Detail'] = value[1]
				if i == 15: profile['Volume'] = value[1]
				if i == 17: profile['Computer Name'] = value[1]
				
			# Extras
			profile['CPU Utilization'] = psutil.cpu_percent()
			
			mem = psutil.virtual_memory()
			profile['Memory Utilization'] = mem.percent
				
			return profile
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))


	###
	def sample_computer_data (self, dev):
		try:
			keyValueList = []
			
			profile = self.sample_computer_profile(dev)
			#indigo.server.log(unicode(profile))
			
			keyValueList.append({'key':'name', 'value':profile['Computer Name']})
			
			keyValueList.append({'key':'model', 'value':u'{} ({})'.format(profile['Model Name'], profile['Model ID'])})
			keyValueList.append({'key':'cpu_model', 'value':profile['CPU']})
			keyValueList.append({'key':'cpu_speed', 'value':profile['CPU Speed']})
			keyValueList.append({'key':'serial', 'value':profile['Serial Number']})
			
			keyValueList.append({'key':'cpu', 'value':profile['CPU Utilization']})
			keyValueList.append({'key':'cpu_count', 'value':profile['Processors']})	
			keyValueList.append({'key':'cpu_cores', 'value':profile['Cores']})
			
			mem = psutil.virtual_memory()
			keyValueList.append({'key':'memory', 'value':mem.total  / 1024 / 1024})
			keyValueList.append({'key':'memory_available', 'value':mem.available / 1024 / 1024})
			keyValueList.append({'key':'memory_percent', 'value':profile['Memory Utilization']})
			
			
			disk = psutil.disk_usage('/')
			keyValueList.append({'key':'disk', 'value':disk.total  / 1024 / 1024})
			keyValueList.append({'key':'disk_available', 'value':disk.free  / 1024 / 1024})
			keyValueList.append({'key':'disk_percent', 'value':disk.percent})
			
			# Not supported in the 1.x that comes with macOS, need to wait until a newer version is out
			#temps = psutil.sensors_temperatures()
			#fans = psutil.sensors_fans()
			#batt = psutil.sensors_battery()
			
			boot = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
			keyValueList.append({'key':'last_boot', 'value':boot})
			
			cmd = [ 'sw_vers', '-productVersion']
			ver = subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0]
			ver = ver.replace("\n","")
			keyValueList.append({'key':'macOS', 'value':ver})
			
			keyValueList.append({'key':'last_sample', 'value':datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
			
			#/usr/sbin/system_profiler SPHardwareDataType | fgrep 'Serial' | awk '{print $NF}'
			
			if dev.pluginProps['state'] == 'cpu': keyValueList.append({'key':'sensorValue', 'value':profile['CPU Utilization'], 'uiValue': u'{}%'.format(profile['CPU Utilization'])})
			if dev.pluginProps['state'] == 'memory_percent': keyValueList.append({'key':'sensorValue', 'value':profile['Memory Utilization'], 'uiValue': u'{}%'.format(profile['Memory Utilization'])})
				
			props = dev.pluginProps
			props['address'] = u'CPU: {}% | Mem: {}%'.format(profile['CPU Utilization'], profile['Memory Utilization'])
			dev.replacePluginPropsOnServer (props)
			
			if keyValueList: dev.updateStatesOnServer(keyValueList)
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	###
	def list_computer_info (self, filter="", valuesDict=None, typeId="", targetId=0): 
		"""
		Return the list of computer stats.
		"""
		
		try:
			listData = []
			if targetId == 0: return listData
			
			dev = indigo.devices[targetId]
			
			listData.append (('name', 'Name:\t\t\t\t{}'.format(dev.states['name'])))
			listData.append (('macOS', 'macOS Version:\t\t{}'.format(dev.states['macOS'])))
			listData.append (('model', 'Model:\t\t\t\t{}'.format(dev.states['model'])))
			listData.append (('cpu_model', 'CPU Info:\t\t\t{} {}'.format(dev.states['cpu_model'], dev.states['cpu_speed'])))
			#listData.append (('serial', 'Serial Number:\t\t{}'.format(dev.states['serial'])))
			listData.append (('serial', 'Serial Number:\t\t{}'.format('XXXXXXXXXX')))
						
			listData.append (('cpu', 'CPU Utilization:\t\t{}%'.format(dev.states['cpu'])))
			listData.append (('cpu_count', 'CPU Count:\t\t\t{}'.format(dev.states['cpu_count'])))
			listData.append (('cpu_cores', 'CPU Cores:\t\t\t{}'.format(dev.states['cpu_cores'])))
			
			listData.append (('memory', 'Memory:\t\t\t\t{} MB'.format("{:,}".format(dev.states['memory']))))
			listData.append (('memory_available', 'Memory Available:\t\t{} MB'.format("{:,}".format(dev.states['memory_available']))))
			listData.append (('memory_percent', 'Memory Used:\t\t{}%'.format(dev.states['memory_percent'])))
			
			listData.append (('disk', 'Pri Drive Capacity:\t\t{} MB'.format("{:,}".format(dev.states['disk']))))
			listData.append (('disk_available', 'Pri Drive Available:\t{} MB'.format("{:,}".format(dev.states['disk_available']))))
			listData.append (('disk_percent', 'Pri Drive Used:\t\t{}%'.format(dev.states['disk_percent'])))
			
			listData.append (('last_boot', 'Last Reboot:\t\t\t{}'.format(dev.states['last_boot'])))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return listData	
		
	###
	def list_computer_states (self, filter="", valuesDict=None, typeId="", targetId=0): 
		"""
		Return the list of computer states.
		"""
		
		try:
			listData = []
			
			listData.append (('cpu', "CPU Usage"))
			listData.append (('memory_available', "Memory Available"))
			listData.append (('memory_percent', "Memory Used %"))
			listData.append (('disk_available', "Disk Available"))
			listData.append (('disk_percent', "Disk Used %"))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return listData				
			
################################################################################
# INDIGO DEVICE METHODS
################################################################################
			
	###
	def validateDeviceConfigUi (self, valuesDict, typeId, devId):
		try:
			errorDict = indigo.Dict()
			dev = indigo.devices[devId]
		
			# While we are here add this device to polling if that is enabled
			if typeId == 'maccmd' or typeId == 'epsmc':
				self.configurePolling (dev, valuesDict)
				self.configurePollingMusic (dev, valuesDict)
				#indigo.server.log(unicode(self.itunespollinglist))
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))	
			
		return (True, valuesDict, errorDict)	
		
	###
	def actionControlDevice(self, action, dev):
		try:
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

		except Exception as e:
			self.logger.error (ex.stack_trace(e))	
			
	###
	def getDeviceConfigUiValues(self, valuesDict, typeId, devId):
		"""
		Indigo function called prior to the form loading in case we need to do pre-calculations.
		"""
		
		try:
			errorsDict = indigo.Dict()
			
			# Set new device defaults
			if typeId == 'maccmd':
				if not 'credentials' in valuesDict: valuesDict['credentials'] = 'manual'
				if not 'onCommand' in valuesDict: valuesDict['onCommand'] = 'runapp'
				if not 'offCommand' in valuesDict: valuesDict['offCommand'] = 'runapp'
				
			elif typeId == 'computer':
				if not 'state' in valuesDict: valuesDict['state'] = 'cpu'
				if not 'credentials' in valuesDict: valuesDict['credentials'] = 'manual'
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))	
			
		return (valuesDict, errorsDict)	
		
	###
	def getActionConfigUiValues(self, valuesDict, typeId, devId):
		"""
		Indigo function called prior to the form loading in case we need to do pre-calculations.
		"""
		
		try:
			errorsDict = indigo.Dict()
			
			# Set new device defaults
			if not 'credentials' in valuesDict: valuesDict['credentials'] = 'manual'
			if not 'onCommand' in valuesDict: valuesDict['onCommand'] = 'runapp'
						
		except Exception as e:
			self.logger.error (ex.stack_trace(e))	
			
		return (valuesDict, errorsDict)					

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
# SAVED CONNECTIONS
################################################################################		

	###
	def get_saved_credential (self, name = '', ip = ''):
		try:
			credentials = self.pluginPrefs['credentials']
			
			for c in credentials:
				item = base64.b64decode(c).split("||")
				if not name == '' and item[0] == name:
					return item
				elif not ip == '' and item[1] == ip:
					return item	
					
			return False
					
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
	
	###
	def save_credential (self, name, ip, user, password):
		try:
			credentials = self.pluginPrefs['credentials']
			newcredentials = []
			
			for c in credentials:
				item = base64.b64decode(c).split("||")
				if not name == '' and item[0] == name:
					return False
					
				newcredentials.append(c)

			item = u'{}||{}||{}||{}'.format(name, ip, user, password)
			newcredentials.append(base64.b64encode(bytes(item)))				
					
			self.pluginPrefs['credentials'] = newcredentials
			
			return True
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			return False
			
	###
	def update_saved_credential (self, name, newname, ip, user, password):
		try:
			credentials = self.pluginPrefs['credentials']
			newcredentials = []
			
			for c in credentials:
				item = base64.b64decode(c).split("||")
				if item[0] == newname and name != newname:
					return False
			
			for c in credentials:
				item = base64.b64decode(c).split("||")
				if (not name == '' and item[0] == name) or (not ip == '' and item[1] == ip):
					item = u'{}||{}||{}||{}'.format(newname, ip, user, password)
					newcredentials.append(base64.b64encode(bytes(item)))
				else:
					newcredentials.append(c)
					
			self.pluginPrefs['credentials'] = newcredentials
			
			return True
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))	

	###
	def action_list_changed (self, valuesDict, typeId):	
		"""
		Drop down list was changed, enable/disable edit fields.
		"""
		
		try:
			errorsDict = indigo.Dict()
			if not 'action' in valuesDict: return (valuesDict, errorsDict)
			
			if valuesDict['action'] == 'delete':
				valuesDict['showfields'] = False
			elif valuesDict['action'] == 'add':
				valuesDict['showfields'] = True
			else:
				valuesDict['showfields'] = False
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))	
			
		return (valuesDict, errorsDict)	

	###
	def action_button_clicked (self, valuesDict, typeId):				
		"""
		User clicked the action button.
		"""
		
		try:
			credentials = self.pluginPrefs['credentials']
			
			errorsDict = indigo.Dict()
			
			if valuesDict['action'] == 'add':
				if not self.save_credential (valuesDict['name'],valuesDict['computerip'],valuesDict['username'],valuesDict['password']):
					errorsDict['showAlertText'] = 'There is already a connection saved as that name, please use a different name.'
					return (valuesDict, errorsDict)	
					
				else:
					valuesDict['name'] = ''
					valuesDict['computerip'] = ''
					valuesDict['username'] = ''
					valuesDict['password'] = ''
			
			elif valuesDict['action'] == 'delete':	
				if not valuesDict['credentials']:
					errorsDict['showAlertText'] = 'You must select which credentials to edit from the list.'
					return (valuesDict, errorsDict)	
				elif len(valuesDict['credentials']) > 1:
					errorsDict['showAlertText'] = 'Too many credentials selected, please select a single credential to edit.'
					return (valuesDict, errorsDict)
				else:
					credentials = self.pluginPrefs['credentials']
					newcredentials = []
			
					for c in credentials:
						item = base64.b64decode(c).split("||")
						if not item[0] == valuesDict['credentials'][0]:
							newcredentials.append(c)

					self.pluginPrefs['credentials'] = newcredentials
				
			elif valuesDict['action'] == 'edit':
				if not valuesDict['showfields']:
					if not valuesDict['credentials']:
						errorsDict['showAlertText'] = 'You must select which credentials to edit from the list.'
						return (valuesDict, errorsDict)	
					elif len(valuesDict['credentials']) > 1:
						errorsDict['showAlertText'] = 'Too many credentials selected, please select a single credential to edit.'
						return (valuesDict, errorsDict)
					else:
						for c in credentials:
							item = self.get_saved_credential (valuesDict['credentials'][0])
							if item:
								valuesDict['name'] = item[0]
								valuesDict['computerip'] = item[1]
								valuesDict['username'] = item[2]
								valuesDict['password'] = item[3]
						
						valuesDict['showfields'] = True	
						
				else:
					if not self.update_saved_credential (valuesDict['credentials'][0], valuesDict['name'],valuesDict['computerip'],valuesDict['username'],valuesDict['password']):
						errorsDict['showAlertText'] = 'There is already a connection saved as that name, please use a different name.'
						return (valuesDict, errorsDict)	
					else:
						valuesDict['name'] = ''
						valuesDict['computerip'] = ''
						valuesDict['username'] = ''
						valuesDict['password'] = ''
						valuesDict['showfields'] = False
					
				
			elif valuesDict['action'] == 'delete':
				pass	
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return (valuesDict, errorsDict)	
		
	###
	def list_credentials (self, filter="", valuesDict=None, typeId="", targetId=0): 
		"""
		Build a custom list of the saved credentials.
		"""
		
		try:
			listData = []
			if filter == 'device': listData = [('manual', 'Manual Login')]
			credentials = self.pluginPrefs['credentials']
			if not credentials: return listData
			
			for c in credentials:
				keyString = base64.b64decode(c)
				#indigo.server.log(u'{}'.format(keyString))
				item = keyString.split("||")
				
				if item[0] != '': listData.append ((item[0], u'{} ({})'.format(item[0], item[1])))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return listData		
		
################################################################################
# FIND EMBEDDED APPLESCRIPT
################################################################################		

	###
	def getMenuActionConfigUiValues(self, menuId):
		valuesDict = indigo.Dict()
		errorMsgDict = indigo.Dict()

		if menuId == 'findApplescript':
			# Set the default DB
			dbdir = '{}/Databases/'.format(indigo.server.getInstallFolderPath())
			dbs = glob.glob(dbdir + "*.indiDb")
			for db in dbs:
				valuesDict['database'] = db.replace(dbdir, "").replace(".indiDb", "")
				break
				
		return (valuesDict, errorMsgDict)		

	###
	def get_databases (self, filter="", valuesDict=None, typeId="", targetId=0):
		"""
		Read database folder for all databases and return them as a list.
		"""
		
		try:
			retList = []
			
			dbdir = '{}/Databases/'.format(indigo.server.getInstallFolderPath())
			dbs = glob.glob(dbdir + "*.indiDb")
			for db in dbs:
				dbname = db.replace(dbdir, "").replace(".indiDb", "")
				retList.append ((dbname, dbname))
				
			return retList
			
		except Exception as e:
			self.logger.error(unicode(e))	
		
	###
	def find_applescript (self):
		try:				
			self.logger.info ('### PLEASE WAIT WHILE YOUR DATABASE IS EXAMINED FOR EMBEDDED APPLESCRIPT, THIS MAY TAKE A MOMENT ###')
			
			# Make copy of the DB
			from shutil import copyfile
			
			dbdir = '{}/Databases/'.format(indigo.server.getInstallFolderPath())
			src = u'{}{}.indiDb'.format(dbdir, indigo.server.getDbName())
			dst = u'{}{}-mccopy.indiDb'.format(dbdir, indigo.server.getDbName())
			
			copyfile(src, dst)
			
			# Parse the DB
			output = '\nThe following items have an embedded AppleScript:\n\n'
			dbdir = '{}/Databases/'.format(indigo.server.getInstallFolderPath())
			xml = cElementTree.iterparse(u'{}{}-mccopy.indiDb'.format(dbdir, indigo.server.getDbName()))
			for event, elem in xml:
				type = ''
				folderId = ''
				id = ''
				name = ''
				script = ''
				isas = False
			
				if elem.tag == "ActionGroup":
					type = 'Action Group'

					for ActionGroup in elem:
						if ActionGroup.tag == 'FolderID': folderId = ActionGroup.text
						if ActionGroup.tag == 'Name': name = ActionGroup.text
						if ActionGroup.tag == 'ID': id = ActionGroup.text
					
						if ActionGroup.tag == 'ActionSteps':
							for ActionSteps in ActionGroup:
								if ActionSteps.tag == 'Action':
									for Action in ActionSteps:
										if Action.tag == 'AppleScriptSCPT':
											isas = True
										if isas and Action.tag == 'ScriptSource':
											script = Action.text
										
				if elem.tag == "Trigger":
					type = 'Trigger'
				
					for Trigger in elem:
						if Trigger.tag == 'FolderID': folderId = Trigger.text
						if Trigger.tag == 'Name': name = Trigger.text
						if Trigger.tag == 'ID': id = Trigger.text	
					
						if Trigger.tag == 'ActionGroup':			
							for ActionGroup in Trigger:
								if ActionGroup.tag == 'FolderID': folderId = ActionGroup.text
								if ActionGroup.tag == 'Name': name = ActionGroup.text
								if ActionGroup.tag == 'ID': id = ActionGroup.text
					
								if ActionGroup.tag == 'ActionSteps':
									for ActionSteps in ActionGroup:
										if ActionSteps.tag == 'Action':
											for Action in ActionSteps:
												if Action.tag == 'AppleScriptSCPT':
													isas = True
												if isas and Action.tag == 'ScriptSource':
													script = Action.text
												
				if elem.tag == "TDTrigger":
					type = 'Schedule'
				
					for Schedule in elem:
						if Schedule.tag == 'FolderID': folderId = Schedule.text
						if Schedule.tag == 'Name': name = Schedule.text
						if Schedule.tag == 'ID': id = Schedule.text	
					
						if Schedule.tag == 'ActionGroup':			
							for ActionGroup in Schedule:
								if ActionGroup.tag == 'FolderID': folderId = ActionGroup.text
								if ActionGroup.tag == 'Name': name = ActionGroup.text
								if ActionGroup.tag == 'ID': id = ActionGroup.text
					
								if ActionGroup.tag == 'ActionSteps':
									for ActionSteps in ActionGroup:
										if ActionSteps.tag == 'Action':
											for Action in ActionSteps:
												if Action.tag == 'AppleScriptSCPT':
													isas = True
												if isas and Action.tag == 'ScriptSource':
													script = Action.text												
						
				if isas and name != '':
					#item = base64.b64decode(script)
			
					#indigo.server.log(u'{}: {} - \n{}'.format(type, name, script))
					#indigo.server.log(u'{}: {}'.format(type, name))
					output += u'{}: {}\n'.format(type, name)
				
					#break
			
			self.logger.info(u'{}'.format(output))
					
			# Remove our DB copy
			os.remove(dst)
					
		except Exception as e:
			self.logger.error (ex.stack_trace(e))			
		
		
################################################################################
# MAC COMMAND RELAY DEVICE
################################################################################	

	###
	def _command (self, dev, method = 'on', props = {}):
		try:
			if not props: props = dev.pluginProps
			onState = True
			if method == 'off': onState = False
		
			# We aren't writing props back, so fill in with saved credentials to pass around
			if 'credentials' in props and props['credentials'] != 'manual':
				item = self.get_saved_credential (props['credentials'])
				if item:
					props['name'] = item[0]
					props['computerip'] = item[1]
					props['username'] = item[2]
					props['password'] = item[3]
					
			command = props["{}Command".format(method)]
								
			if command == "none":
				return
				
			elif command == "runapp":
				self.openApp (dev, method, props)
				if not dev is None: 
					dev.updateStateOnServer("onOffState", onState)
					self.configurePolling (dev, props)
					
			elif command == "quitapp":
				self.quitApp (dev, method, props)
				if not dev is None: 
					dev.updateStateOnServer("onOffState", onState)
					self.configurePolling (dev, props)
					
			elif command == "sleep":
				self.sleepComputer (dev, method, props)
				if not dev is None: 
					dev.updateStateOnServer("onOffState", onState)
					self.configurePolling (dev, props)
					
			elif command == "restart":
				self.restart_computer (dev, method, props)
				if not dev is None: 
					dev.updateStateOnServer("onOffState", onState)
					self.configurePolling (dev, props)
					
			elif command == "update":
				thread.start_new_thread (self.update_computer, (dev, method, props))
				
			elif command == "shutdown":
				self.shutdown_computer (dev, method, props)
				if not dev is None: 
					dev.updateStateOnServer("onOffState", onState)
					self.configurePolling (dev, props)			
					
			elif command == "screensaver":
				self.screenSaver (dev, method, props)
				if not dev is None: 
					dev.updateStateOnServer("onOffState", onState)
					self.configurePolling (dev, props)
					
			elif command == "showmessage":
				self.send_message (dev, method, props)
				
			elif command == "builtin":
				if props["{}Standard".format(method)] == "playpause":
					self.playPause (dev, method, props)
				if props["{}Standard".format(method)] == "playlist":
					self.playList (dev, method, props)
				if props["{}Standard".format(method)] == "startitunes":
					self.startStopiTunes (dev, "start", props)
				if props["{}Standard".format(method)] == "stopitunes":
					self.startStopiTunes (dev, "stop", props)
			
				# Since this was an ON command, turn it on
				if not dev is None:
					dev.updateStateOnServer("onOffState", onState)
					self.configurePolling (dev, props)

		except Exception as e:
			self.logger.error (ex.stack_trace(e))	

	###
	def command_turn_on (self, dev, props = {}):
		try:
			self._command (dev, 'on', props)

		except Exception as e:
			self.logger.error (ex.stack_trace(e))
		
	###
	def command_turn_off (self, dev, props = {}):
		try:
			self._command (dev, 'off', props)

		except Exception as e:
			self.logger.error (ex.stack_trace(e))			
		
		
	###
	def ssh (self, props, activity):
		"""
		Establish SSH to remote computer and return the prompt.
		"""
		try:
			if not props["localhost"]:
				s = pxssh.pxssh()
				if not s.login (props["computerip"], props["username"], props["password"]):
					self.logger.error ("SSH session failed to login to '{}'.  Check your IP, username and password and make sure you can SSH to that computer from the Indigo server.".format(props['credentials'][0]))
					return False
					
				#rootprompt = re.compile('.*[$#]')	
				#i = self.expect(["(?i)are you sure you want to continue connecting", "(?i)(?:password)|(?:passphrase for key)", "(?i)permission denied", "(?i)terminal type", "(?i)connection closed by remote host"], timeout=20)
				#indigo.server.log(u'{}'.format(i))
				s.sendline('sudo -s')
				s.sendline(props["password"])
				
				return s
			
			else:
				self.logger.error ("{} the Indigo computer is not currently supported".format(activity))
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return None	
		
	###
	def list_commands (self, filter="", valuesDict=None, typeId="", targetId=0): 
		"""
		Return the list of all commands.
		"""
		
		try:
			listData = []
			listData.append (('none', '- Do Nothing -'))
			listData.append (('runapp', 'Run Application'))
			listData.append (('quitapp', 'Quit Application'))
			listData.append (('showmessage', 'Display Notification Message'))
			listData.append (('screensaver', 'Start Screensaver'))
			listData.append (('restart', 'Restart Computer'))
			listData.append (('sleep', 'Sleep Computer'))
			listData.append (('shutdown', 'Turn Off Computer'))
			listData.append (('update', 'Install Software Updates'))
			listData.append (('builtin', 'iTunes'))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return listData				
		
################################################################################
# APPLESCRIPT HANDLER MIGRATED METHODS
################################################################################				

	###
	def run_custom_applescript (self, action):
		"""
		Run an custom AppleScript code from Actions.
		"""
		
		# Remove any Control-Enter's from the text, they corrupt the script
		script = ''
		msg = '\n'
		idx = 1
		for s in action.props['script']:
			msg += u'{}: {} ({})\n'.format(idx, ord(s), s)
			idx = idx + 1
			
			if ord(s) != 8232:
				script += s

		#indigo.server.log(msg)
		#indigo.server.log(script)
		#return
				
		script = applescript.AppleScript(source=script)
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
# MAC COMMANDER UI FUNCTIONS
################################################################################
			
	###
	def commander_field_changed (self, valuesDict, typeId, devId = ''):
		"""
		Triggers form actions.
		"""
		
		try:
			errorsDict = indigo.Dict()
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))	
			
		return (valuesDict, errorsDict)					
	
			
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
			props = devAction.props
			
			# We aren't writing props back, so fill in with saved credentials to pass around
			if 'credentials' in props and props['credentials'] != 'manual':
				item = self.get_saved_credential (props['credentials'])
				if item:
					props['name'] = item[0]
					props['computerip'] = item[1]
					props['username'] = item[2]
					props['password'] = item[3]
					
			self.send_message (None, '', props)
			
		elif action == 'command':
			self.command_turn_on(None, devAction.props)
				
		else:
			return
			
	###
	def sleepComputer (self, dev, method, props = {}):
		#cmd = " -e 'sleep'"
		#cmd = self.encapsulateCmd (dev, cmd, "Finder", "Finder", props)
		#result = self.runOsa (cmd)
		
		try:
			s = self.ssh (props, "Sleeping")
			if s:		
				s.sendline ('pmset sleepnow')
				
				s.prompt() 
				s.logout()
				
		except Exception as e:
			self.logger.error (ex.stack_trace(e))	
		
	###
	def restart_computer (self, dev, method, props = {}):
		try:
			if not props: props = dev.pluginProps
			
			s = self.ssh (props, "Rebooting")
			if s:		
				s.sendline ('sudo shutdown -r now')
				
				s.prompt() 
				s.logout()
				
		except Exception as e:
			self.logger.error (ex.stack_trace(e))	
			
	###
	def shutdown_computer (self, dev, method, props = {}):
		try:
			if not props: props = dev.pluginProps
			
			s = self.ssh (props, "Shutting down")
			if s:		
				s.sendline ('sudo shutdown -h now')
				
				s.prompt() 
				s.logout()
				
		except Exception as e:
			self.logger.error (ex.stack_trace(e))	
			
	###
	def update_computer (self, dev, method, props = {}):
		try:
			if not props: props = dev.pluginProps
			
			s = self.ssh (props, "Update")
			if s:		
				s.sendline ('sudo softwareupdate -iaR')
				
				try:
					s.prompt(timeout=1200) 
					s.logout()
				except Exception as ex:
					pass # if we rebooted then it may time out	
				
				
		except Exception as e:
			self.logger.error (ex.stack_trace(e))				
		
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
		if not props: props = dev.pluginProps
		cmd = " -e 'quit'"
		cmd = self.encapsulateCmd (dev, cmd, "Finder", props[method + "Appname"], props)
		
		result = self.runOsa (cmd)
		#indigo.server.log(u"{}".format(result))
		
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
		#indigo.server.log(u'{}'.format(cmd))
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
				
		
		
	

	
