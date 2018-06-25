"""version.py: Plugin version control."""

__version__ 	= "1.0.0"

__modname__		= "Version Control"
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
import requests
from distutils.version import LooseVersion
from datetime import datetime, timedelta, time

# Third Party Modules
import indigo

# Package Modules
import ex

# Enumerations
INDIGO_API_URL = 'https://api.indigodomo.com/api/v2/pluginstore/plugin-version-info.json?pluginId={}'
INDIGO_STORE_URL = 'https://www.indigodomo.com/pluginstore/{}/'
ON_PLUGIN_STORE = True

###		
def version_check(pluginBase):
	global ON_PLUGIN_STORE
	if not ON_PLUGIN_STORE: return # We've already tried to check and failed, do not check again
	
	# Create some URLs we'll use later on
	pluginId = pluginBase.pluginId
	current_version_url = INDIGO_API_URL.format(pluginId)
	store_detail_url = INDIGO_STORE_URL
	pluginBase.next_version_check = datetime.now() + timedelta(days=1)
	
	try:
		# GET the url from the servers with a short timeout (avoids hanging the plugin)
		reply = requests.get(current_version_url, timeout=5)
		# This will raise an exception if the server returned an error
		reply.raise_for_status()
		# We now have a good reply so we get the json
		reply_dict = reply.json()
		plugin_dict = reply_dict["plugins"][0]
		# Make sure that the 'latestRelease' element is a dict (could be a string for built-in plugins).
		latest_release = plugin_dict["latestRelease"]
		if isinstance(latest_release, dict):
			# Compare the current version with the one returned in the reply dict
			if LooseVersion(latest_release["number"]) > LooseVersion(pluginBase.pluginVersion):
				# The release in the store is newer than the current version.
				# We'll do a couple of things: first, we'll just log it
				pluginBase.logger.error(
					"A new version of {} (v{}) is available at: {}".format(
						pluginBase.pluginDisplayName,
						latest_release["number"],
						store_detail_url.format(plugin_dict["id"])
					)
				)
				# We'll change the value of a variable named "Plugin_Name_Current_Version" to the new version number
				# which the user can then build a trigger on (or whatever). You could also insert the download URL,
				# the store URL, whatever.
				try:
					variable_name = "u{}_Current_Version".format(pluginBase.pluginDisplayName.replace(" ", "_"))
					indigo.variable.updateValue(variable_name, latest_release["number"])
				except:
					pass
				# We'll execute an action group named "New Version for Plugin Name". The action group could
				# then get the value of the variable above to do some kind of notification.
				try:
					action_group_name = "New Version for {}".format(pluginBase.pluginDisplayName)
					indigo.actionGroup.execute(action_group_name)
				except:
					pass
				# There are lots of other things you could do here. The final thing we're going to do is send
				# an email to self.version_check_email which I'll assume that you've set from the plugin
				# config.
				if hasattr(self, 'version_check_email') and self.version_check_email:
					indigo.server.sendEmailTo(
						pluginBase.version_check_email, 
						subject="New version of Indigo Plugin '{}' is available".format(pluginBase.pluginDisplayName),
						body="It can be downloaded here: {}".format(store_detail_url)
					)
				
			else:
				pluginBase.logger.info(u"{} is running the latest version, no update needed".format(pluginBase.pluginDisplayName))

		
	except Exception as e:
		if "Not Found for url" in unicode(e):
			ON_PLUGIN_STORE = False
			pluginBase.logger.debug(u"{} is not on the Indigo Plugin Store, update checking disabled".format(pluginBase.pluginDisplayName))
		else:
			pluginBase.logger.error(ex.stack_trace(e))












