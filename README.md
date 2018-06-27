![](https://github.com/Colorado4Wheeler/WikiDocs/blob/master/Mac-Commander/Logo.png)


# Mac Commander

This plugin for the [Indigo Domotics](http://www.indigodomo.com/) home automation platform that allows you to execute any AppleScript command on the Indigo server or any other Mac on your network remotely.  Essentially, if you can do something via AppleScript then you can use Mac Commander.

The plugin also allows you to create custom AppleScript scripts directly in the plugin just as you have been able to in Indigo.  While not as robust as the Indigo editor it is still fully functional and allows you to either code from scratch or copy-and-paste your AppleScript code directly into the plugin for use.

Mac Commander is **not** all about AppleScript, it's about any means of controlling remote Macs, including utilizing shell commands when AppleScript has no function (such as for rebooting computers or putting them to sleep).  While AppleScript is a large part of Mac Commander it is only a part.

While version 1.1.0 and prior required having a Mac Commander device in Indigo, version 2.x forward allows you to either create a device in Indigo or never create a device and perform all functions of this plugin as actions, eliminating the need to have lots of virtual devices in your Indigo setup.

## What Can It Do?

Here are the things you can do with Mac Commander:

* Create a relay device (on/off) where both On and Off can perform any of the things on this list independently
* Perform any of the things on this list as an acton with **zero** devices required, everything can be performed via an action
* Run an application on any Mac in any network (so long as you have access and permissions)
* Quit an application on any Mac in any network
* Display a notification message on any Mac in any network
* Start the screensaver on any Mac in any network
* Put any Mac on any network to sleep
* Reboot any Mac on any network
* Shut down any Mac on any network
* Perform an Apple App Store software update automatically and without prompting on any Mac on any network (and even auto reboot if/when needed)
* Perform text-to-speech on any Mac in any network
* Play, Pause, Start and Stop iTunes on any Mac on any network
* Run a saved AppleScript .scpt file saved on your Indigo computer
* Run a custom written AppleScript code from your Indigo computer (what it does could be directed anywhere)
* **Find all embedded AppleScript scripts that are on any Indigo schedule, action group or trigger so you can get those migrated to Python**

## Requirements

In order to utilize this plugin on a remote Mac you will need to enable Remote Login and Remote Apple Events on the remote Mac in the Sharing Preferences for that Mac.  This is not needed if you are only going to use this plugin to control your Indigo computer.

This requires Indigo 7 to run but there is a legacy version that is no longer updated (but still fully functional) that supports Indigo 6 and earlier.

## EPS AppleScript Handler

The AppleScript Handler plugin was created as a means for users to run AppleScripts as Indigo phases out AppleScript support.  That plugin is now rolled into Mac Commander and will be sunsetted.
