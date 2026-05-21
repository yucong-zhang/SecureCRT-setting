#$language = "Python"
#$interface = "1.0"

# ColorSchemeAutoRotation.py
#   Last Modified: 13 Oct 2017
#     - Now works with new color scheme options available in 8.3.x
#       and newer versions of SecureCRT.
#     - Use more reliable mechanism for retrieving the configuration
#       path through use of GetConfigPath() custom method.
#
#   Last Modified: 05 Sep 2013
#     - Initial Revision
#
# Description:
#   This script will automatically rotate to the next Color Scheme
#   each time a connection is made with the current session.
#   For example (in a default SecureCRT configuration), if the
#   color scheme for the current session is currently set to
#   "Black / Cyan", the color scheme will automatically be
#   set to "Floral White / Dark Cyan".  The next time the
#   session is used for making a connection, the color
#   scheme will change from "Floral White / Dark Cyan" to
#   "White / Black", and so on each time the session is used
#   to connect.
#
#   Although it is suggested that you use this script as a logon script
#   you can also choose to create a button to run the script manually
#   (for example if you don't like the current color scheme and want to
#   manually rotate to the next one).  For information on creating a
#   button to run this script, read through the button bar tip online:
#      https://www.vandyke.com/support/tips/buttonbar.html
#
#   ... or view the Button Bar video on the VanDyke Software YouTube
#   channel:
#      https://www.youtube.com/VandykeSoftware
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import os, sys, platform, re
import codecs

crt.Session.SetStatusText("")

MsgBox = crt.Dialog.MessageBox

# Preload a list of existing color schemes from the configuration
# location specified in the user's registry.
bColorsLoadedFromConfig = False

# Set up two dictionaries for use in collecting color scheme names
# and cross-referencing each name with an index so that the color
# scheme rotation is much easier (we can deal with indices/numbers
# instead of names).
g_cColorSchemes = {}
g_cSchemeIndices = {}

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():
    # Make our global variables available to us in this routine
    global bColorsLoadedFromConfig
    global g_cColorSchemes
    global g_cSchemeIndices

    strConfigPath = GetConfigPath()

    strVersion = crt.Version
    strVersionPart = strVersion.split(" ")[0]
    vVersionElements = strVersionPart.split(".")
    nMajor = vVersionElements[0]
    nMinor = vVersionElements[1]
    nMaintenance = vVersionElements[2]

    if strConfigPath == "":
        MsgBox(
            "Error: Unable to determine location of current configuration " +
            "path in order to load existing color schemes.\r\n\r\n" +
            "You're probably running SecureCRT with a configuration folder " +
            "that exists where SecureCRT.exe lives, or you're running with " +
            "the /F <special_path_to_config_folder> option, and we can't " +
            "cope with that in SecureCRT yet.\r\n\r\n" +
            "Script is unable to proceed further.")
        return

    if float("{0}.{1}".format(nMajor, nMinor)) >= 8.3:
        if os.path.isfile(strConfigPath + "/Global.ini"):
            # Load color schemes now from Global.ini file:
            # Example contents:
                #Z:"Color Schemes"=00000016
                # Solarized Light,010101,...,Solarized Light
                # Birds of Paradise,010101,E0DBB700,...,Birds of Paradise
                # Black / Cyan,010101,00000000,...,Standard
                # Black / Floral White,010101,00000000,...,Standard
                # Chalkboard,010101,D9E6F200,D9E6F200...,Chalkboard
                # Ciapre,010101,AEA47A00,...,Ciapre
                # ...
            regexp = re.compile("(Z\:\")(.*?)(\"=)([a-zA-Z0-9]+)", re.I + re.M)
            with codecs.open(strConfigPath + "/Global.ini", "r", "utf-8") as objFile:
                #with open(strConfigPath + "/Global.ini", "r") as objFile:
                nCurLine = 0
                nIndex = 0
                strLastButtonBarName = ""
                nSubLinesToRead = 0
                bReadingSubLines = False
                for strLine in objFile:
                    nCurLine += 1
                    if bReadingSubLines:
                        nSubLinesToRead -= 1
                        strColorSchemeName = strLine.split(",")[0].strip()
                        if not strColorSchemeName in g_cColorSchemes:
                            g_cColorSchemes[strColorSchemeName] = nIndex
                            g_cSchemeIndices[nIndex] = strColorSchemeName
                            if not bColorsLoadedFromConfig:
                                bColorsLoadedFromConfig = True
                            nIndex += 1
                        if nSubLinesToRead <= 0:
                            bReadingSubLines = False
                            break
                    else:
                        objMatch = regexp.search(strLine)
                        if objMatch:
                            strOptionName = objMatch.group(2)
                            strSubLineCount = objMatch.group(4)
                            nNumSubLines = int("0x{0}".format(strSubLineCount), 0)
                            nSubLinesToRead = nNumSubLines
                            if strOptionName == "Color Schemes":
                                bReadingSubLines = True

            if not bColorsLoadedFromConfig:
                MsgBox("{0}\r\n\r\n{1}".format(
                    "Color Scheme data is not yet available in Global.ini file.",
                    "Please close SecureCRT and try again."))
                return

        else:
            MsgBox("Unable to locate Global.ini file in config path: " +
                strConfigPath)
            return

    else:
        if os.path.isfile(strConfigPath + "/Color Schemes.ini"):
            strColorSchemeData = ""
            with codecs.open(strConfigPath + "/Color Schemes.ini", "r", "utf-8") as objFile:
                strColorSchemeData = objFile.read()

            # MsgBox(strColorSchemeData)
            # Now, let's use a regular expression to parse
            # out all the color scheme names from this file.
            # RegExp pattern for color schemes:
            #   B:"colorSchemeName"=00000044
            regexp = re.compile('[\s\S]*?B\:\"(.*?)\"=\d+', re.I + re.M)

            # Now let's iterate through all the color scheme names and populate
            # two dictionaries (hash tables) one indexed by scheme name, the
            # other by index of appearance (so that rotating is easier -- by
            # knowing where we are currently, it will be easier to find out the
            # next one in line):
            nIndex = 0
            for strColorSchemeName in regexp.findall(strColorSchemeData):
                if not strColorSchemeName in g_cColorSchemes:
                    g_cColorSchemes[strColorSchemeName] = nIndex
                    g_cSchemeIndices[nIndex] = strColorSchemeName
                    if not bColorsLoadedFromConfig:
                        bColorsLoadedFromConfig = True
                    nIndex += 1
        else:
            MsgBox("Unable to locate Color Schemes.ini file in config path: " +
                strConfigPath)
            return


    # Find out if we were able to read in any successful color schemes.
    if len(g_cColorSchemes) < 1:
        MsgBox("Color Schemes collection is empty!\r\nVersion {0}.{1}.{2}".format(nMajor, nMinor, nMaintenance))
        return

    # Get a reference to the current script tab so that we can be "tab safe"
    objCurTab = crt.GetScriptTab()

    # Get the current color scheme setting:
    strCurColorScheme = objCurTab.Session.Config.GetOption("Color Scheme")
    if strCurColorScheme in g_cColorSchemes:
        # Use the color scheme's index (position as defined in the .ini
        # file) instead of its name when performing rotations.
        nIndex = g_cColorSchemes[strCurColorScheme] + 1

        # This is where we rotate from the bottom of the list back
        # up to the top.  Since our hash table (dictionary) has indexes
        # at each value, we'll simply start at 0 (zero) if our index is
        # past the end of the index of the last color scheme defined.
        if nIndex >= len(g_cColorSchemes):
            nIndex = 0
    else:
        # start at the beginning of the list if somehow the session config
        # has an unknown/non-existent color scheme:
        nIndex = 0

    # crt.Session.SetStatusText("nIndex = {0}".format(nIndex))
    # MsgBox(str(g_cSchemeIndices))
    # Convert the index we have into a color scheme name
    strNewColorScheme = g_cSchemeIndices[nIndex]

    objCurTab.Session.Config.SetOption("Color Scheme", strNewColorScheme)
    bAnsiColorEnabled = objCurTab.Session.Config.GetOption("ANSI Color")
    if not bAnsiColorEnabled:
        objCurTab.Session.Config.SetOption("ANSI Color", True)

    bColorSchemeOverridesANSI = objCurTab.Session.Config.GetOption("Color Scheme Overrides Ansi Color")
    if not bColorSchemeOverridesANSI:
        objCurTab.Session.Config.SetOption("Color Scheme Overrides Ansi Color", True)

    # Reflect the chosen color scheme name in the status bar
    # so the operator can know it by name.
    crt.Session.SetStatusText(strNewColorScheme)

    objCurTab.Session.Config.Save()


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def GetConfigPath():
    objConfig = crt.OpenSessionConfiguration("Default")
    # Try and get at where your configuration folder is located
    strOptionName = "Upload Directory V2"
    strOrigValue = objConfig.GetOption(strOptionName)

    objConfig.SetOption(strOptionName, "${VDS_CONFIG_PATH}")
    # Make the change, so that the above templated name will get written
    # to the config...
    objConfig.Save()

    # Now, load a fresh copy of the config, and pull the option... so
    # that SecureCRT will convert from the template path value to the
    # actual path value:
    objConfig = crt.OpenSessionConfiguration("Default")
    strConfigPath = objConfig.GetOption(strOptionName)

    # Now, let's restore the setting to its original value
    objConfig.SetOption(strOptionName, strOrigValue)
    objConfig.Save()

    # Now return the config path
    return strConfigPath



main()