Current Release Notes
==========

Version 2.0.0-b5
---------------
* Fixed error loading library that was preventing the plugin from fully initializing

Previous Release Notes
==========

Version 2.0.0-b4
---------------
* Added new plugin menu option [Find Embedded AppleScript](https://github.com/Colorado4Wheeler/Mac-Commander/wiki/Plugin-Menu-Commands#find-embedded-applescript) in Indigo to locate all Indigo items that have an embedded ApplesScript so you can get those functions reprogrammed in Python

Version 2.0.0-b3
---------------
* Added new [Saved Connections](https://github.com/Colorado4Wheeler/Mac-Commander/wiki/Saved-Connections) option in the menu to save commonly used credentials
* Added ability for all forms to utilize the new [Saved Connections](https://github.com/Colorado4Wheeler/Mac-Commander/wiki/Saved-Connections) data
* Added sleep, reboot and shutdown via SSH as available commands
* Added software updates as a command
* Removed all credential field defaults
* Fixed bug in Command action that would cause an error when trying to quit an app

Version 2.0.0-b2
---------------
* Added Plugin Store update check
* Added Custom AppleScript action with a full AppleScript editor built in so you can write scripts on the fly and run them (or copy and paste them, up to you)
* Cleaned up action list with separators to delineate the commands more


Version 2.0.0-b1
---------------
* Added second Mac Commander device as a relay so it could be turned on and off via the Indigo UI, the previous version used a custom device and the only way to turn that on or off was via a UI action (action group, schedule, trigger).  The old method will stay in the plugin for now to support upgrades but shouldn't be used as it will be phased out in a future version.
* Added new action to send notification to a remote system (independant, requires no device), useful if you want to notify your workstation of something that just happened on the Indigo server (or anything else for that matter)
* Commands can now be run via an action and no longer requires a device (however devices still exist if preferred)
* Removed commands to reboot or sleep the remote computer because Apple no longer allows those commands remotely (but can be done in a local AS that Mac Commander can run remotely)
* Modernized the UI
* Changed 1.x actions to have a prefix of Legacy so as not to be confused with the new devices
* Merged the AppleScript Handler plugin into Mac Commander (be sure to move your scripts to /Library/Application Support/Perceptive Automation/Indigo 7/Preferences/Plugins/com.eps.indigoplugin.mac-commander if you saved them for AppleScript Handler)
* From AppleScript Handler: added action to run scripts saved to the plugin prefs folder
* Version 1.x code cleanup
* Fixed bug where Quit App would not run the application command to quit
* Fixed bug where turning a command off may not be reflected in the UI or device state
* Fixed bug where displaying a message would not show the message on the remote system due to changes in AppleScript, it will now show a notification instead

Development Notes
==========

Known Issues As Of The Most Current Release
---------------

* About link for devices point to the generic Indigo page
* Using special characters in your password will fail, such as backslash, apostrophe and double quotes

Wish List
---------------

* Check if a user is logged into the remote computer
* Shutdown, sleep, restart, wake functions