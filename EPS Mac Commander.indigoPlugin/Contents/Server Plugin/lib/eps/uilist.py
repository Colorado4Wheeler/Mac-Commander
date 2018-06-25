"""uilist.py: Calculated custom lists and menus for UI forms."""

__version__ 	= "3.0.0"

__modname__		= "UI List"
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

# Third Party Modules
import indigo

# Package Modules
from lib.eps import ex

# Enumerations
JSON_FIELD = 'libJSONData'

class UIList:
	"""
	Methods to configure and control the Sensor device.
	"""
	
	def __init__(self, plugin):
		"""
		Start the factory with references back to the base plugin.
		
		Arguments:
		plugin: 			Indigo plugin
		"""
	
		try:
			if plugin is None: return # pre-loading before init
			
			self.logger = logging.getLogger ("Plugin.{}".format(self.__class__.__name__.replace("_","")))
			
			self.plugin = plugin	# References the Indigo plugin
		
			self.logger.debug ("{} {} loaded".format(__modname__, __version__))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	###
	def format_list_column_entry (self, columndefs, columndata):
		"""
		Return a list item formatted to comply with the column definitions.
		
		Arguments:
			columndefs:				(list) maximum spaces per column
			columndata:				(list) the data to enter into the columns
			
		Returns:
			list representative of the column configuration
		"""
		
		try:
			colidx = 0
			output = ""
			
			for c in columndata	:
				length = columndefs[colidx]
				if len(str(c)) > (length):
					# Shorten the value so it fits, it should be tabs * 4 - 1 to leave a space between columns
					x = (length) - 1 # Shorten by one extra for space between columns
					x = x - 3 # Shorted by 3 more so we can add '...' to let the user know its been truncated
					c = c[0:x] + "..."

				column = u"{}".format(c).ljust(length)
				output += column

				colidx = colidx + 1

			return output
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))			
			
	###
	def format_list_column_entry_tabs (self, columndefs, columndata):
		"""
		Return a list item formatted to comply with the column definitions.
		
		Arguments:
			columndefs:				(list) maximum tabs (4 spaces) per column
			columndata:				(list) the data to enter into the columns
			
		Returns:
			list representative of the column configuration
		"""
		
		try:
			colidx = 0
			output = ""
			
			for c in columndata	:
				tabs = columndefs[colidx]
				if len(str(c)) > (tabs * 4):
					# Shorten the value so it fits, it should be tabs * 4 - 1 to leave a space between columns
					x = (tabs * 4) - 1 # Shorten by one extra for space between columns
					x = x - 3 # Shorted by 3 more so we can add '...' to let the user know its been truncated
					c = c[0:x] + "..."

				if len(str(c)) > 23:
					tabs = tabs - 6
				elif len(str(c)) > 19:
					tabs = tabs - 5
				elif len(str(c)) > 15:
					tabs = tabs - 4
				elif len(str(c)) > 11:
					tabs = tabs - 3
				elif len(str(c)) > 7:
					tabs = tabs - 2
				elif len(str(c)) > 3:
					tabs = tabs - 1
					
				if tabs < 1: tabs = 1 # Failsafe in case we got messed up
				
				tabstring = ""

				for i in range (0, tabs):
					tabstring += "\t"

				column = u"{}{}".format(c, tabstring)
				output += column

				colidx = colidx + 1

			return output
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			