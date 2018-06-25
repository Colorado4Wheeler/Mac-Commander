"""jstuff.py: Saves data in hidden form fields in JSON format."""

__version__ 	= "3.0.0"

__modname__		= "JSON Stuffer"
__author__ 		= "ColoradoFourWheeler"
__copyright__ 	= "Copyright 2018, ColoradoFourWheeler & EPS"
__credits__ 	= ["ColoradoFourWheeler"]
__license__ 	= "GPL"
__maintainer__ 	= "ColoradoFourWheeler"
__email__ 		= "Indigo Forums"
__status__ 		= "Production"

# Python Modules
import logging
import sys
import json
import hashlib 
import operator
from random import randint
import datetime
#from datetime import date, timedelta
import re
import ast

# Third Party Modules
import indigo

# Package Modules
from lib.eps import ex

# Enumerations
JSON_FIELD = 'libJSONData'

class JsonStuffer:
	"""
	Methods to configure and control the Sensor device.
	"""
	
	def __init__(self, plugin, name = '', structure = [], obj = None):
		"""
		Start the factory with references back to the base plugin.
		
		Arguments:
		plugin: 			Indigo plugin
		name:				(str) JSON record name
		structure:			(list) JSON record structure
		"""
	
		try:
			if plugin is None: return # pre-loading before init
			
			self.logger = logging.getLogger ("Plugin.{}".format(self.__class__.__name__.replace("_","")))
			
			self.plugin = plugin	# References the Indigo plugin
			self.records = [] # All JSON records for this type
			
			if not "jkey" in structure: structure.append("jkey")
			
			self.structure = structure # Record structure for this data type
			self.recordName = name
			
			self.obj = obj
		
			self.logger.debug ("{} {} loaded".format(__modname__, __version__))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	###
	def _create_hash_key (self, keyString):
		"""
		Create a 256K hash key from the provided string.
		
		Aguments:
			keyString:			(str) string to use for unique hash value
			
		Returns:
			string				value of hashed keyString
		"""
			
		try:
			hashKey = hashlib.sha256(keyString.encode('ascii', 'ignore')).digest().encode("hex")  # [0:16]
			return hashKey	
				
		except Exception as e:
			self.logger.error (ex.stack_trace(e))	
			return ""
			
	##
	def create_unique_key (self):
		"""
		Create a unique identifier (key) using the date and time to the millisecond plus a random number to ensure uniqueness.
		
		Returns:
			string				value of hashed keyString
		"""
		
		try:
			d = indigo.server.getTime()
			key = self._create_hash_key (d.strftime("%Y-%m-%d %H:%M:%S %f") + str(randint(1000, 1000001)))
			key = key[0:16]
			return key
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return ""
		
	###
	def set_form_records (self, valuesDict):
		"""
		Look for the presense of the JSON_FIELD in the form data and retrieve it or create a blank dictionary.  This can be called
		from a child process to force the record list into the variable so it can be iterated.
		"""
		
		try:
			if not JSON_FIELD in valuesDict:
				allrecords = {}
				valuesDict[JSON_FIELD] = json.dumps(allrecords)
			
			allrecords = json.loads(valuesDict[JSON_FIELD])
			
			if not self.recordName in allrecords:
				allrecords[self.recordName] = []
			
			self.records = allrecords[self.recordName]
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	###
	def clear_form_records (self, valuesDict):
		"""
		Empty the current record name in the JSON records and start it fresh.
		"""
		
		try:
			self.set_form_records (valuesDict)
			self.records = []
			self.apply_form_records (valuesDict)
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return valuesDict
			
	###
	def apply_form_records (self, valuesDict):
		"""
		JSON encode the current record set into the larger record set and save it to valuesDict.
		
		Arguments:
			valuesDict				(dict) dictionary of form values to read from and write to
			
		Returns:
			dict					valuesDict modified
		"""
		
		try:
			currentrecords = self.records
			self.set_form_records (valuesDict) # Always refresh in case another process updated a record
			
			if not JSON_FIELD in valuesDict:
				allrecords = {}
				valuesDict[JSON_FIELD] = json.dumps(allrecords)
				
			allrecords = json.loads(valuesDict[JSON_FIELD])	
			allrecords[self.recordName] = currentrecords
				
			valuesDict[JSON_FIELD] = json.dumps(allrecords)	
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return valuesDict
			
		
			
	###
	def add_record (self, record, valuesDict):
		"""
		Add record to the current record name that was passed on initialization.
		
		Arguments:
			record:				(list) field data in the same order as the structure passed during init
			valuesDict			(dict) dictionary of form values
		"""
	
		try:
			self.set_form_records (valuesDict)
			
			rec = {}
			rec["jkey"] = self.create_unique_key()
			
			for i in range (0, len(record)):
				rec[self.structure[i]] = record[i]
				
			self.records.append (rec)		
			valuesDict = self.apply_form_records(valuesDict)
			
			
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return valuesDict