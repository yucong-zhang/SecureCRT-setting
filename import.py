# $language = "Python"
# $interface = "1.0"

# This script aims to simplify the process of importing someone else's
# keyword highlighting INI file by walking the individual through the
# process of browsing to the INI file, automatically creating the
# Keywords folder in the user's Config folder, copying the INI file
# into the correct location, and then setting the current session
# cofiguration to use the file with color highlighting enabled in
# session options.
#
# Last Modified:
#
#   04 Feb, 2022
#     - Modified code to work with either Python 2 or Python 3
#       ("<>" doesn't exist in Python 3, so use 'not ... == ...')
#
#   09 Mar, 2020
#     - Use os.path.expandvars() in GetConfigPath() to
#       return the resolved version of the configuration
#       path in case it has any variables in it.
#     - By default, enable bold and color attribs, but not
#       reverse.
#
#   24 May, 2018
#     - Wrap file system operations in try/except blocks to
#       fail "nicely" if the individual doesn't happen to
#       have permissions to create folders or files in
#       SecureCRT's configuration folder, or read the .ini
#       file specified.
#     - Offer user options of overwriting, saving as a new
#       name (auto- matically generated to be unique), or
#       canceling altogether if a keyword file of the same
#       name already exists in the config folder's Keywords
#       directory.
#     - Create the Keywords folder in the Configuration
#       directory only if we've proceded to the point where
#       we're about to copy the INI file into place. This
#       way, if the individual cancels the script, we won't
#       have made changes that need to be undone.

import os
import shutil
import time, datetime

global g_strConfigPath
g_strConfigPath = ""

def IsSessionReadOnly(strSessionPath):

    objConfig = crt.OpenSessionConfiguration(strSessionPath)

    strOptionName = "Upload Directory V2"
    strOrigValue = objConfig.GetOption(strOptionName)

    strTimeStamp = time.time()
    strDateTime = datetime.datetime.fromtimestamp(strTimeStamp).strftime('%Y%m%d_%H%M%S.%f')[:-3]
    objConfig.SetOption(strOptionName, strDateTime)
    objConfig.Save()

    objConfig = crt.OpenSessionConfiguration(strSessionPath)
    strNewValue = objConfig.GetOption(strOptionName)

    # Now, let's restore the setting to its original value
    objConfig.SetOption(strOptionName, strOrigValue)
    objConfig.Save()

    if not strNewValue == strDateTime:
        return True
    else:
        return False

def GetConfigPath():
    objConfig = crt.OpenSessionConfiguration("Default")
    # Try and get at where the configuration folder is located. To achieve
    # this goal, we'll use one of SecureCRT's cross-platform path
    # directives that means "THE path this instance of SecureCRT
    # is using to load/save its configuration": ${VDS_CONFIG_PATH}.

    # First, let's use a session setting that we know will do the
    # translation between the cross-platform moniker ${VDS_CONFIG_PATH}
    # and the actual value... say, "Upload Directory V2"
    strOptionName = "Upload Directory V2"

    # Stash the original value, so we can restore it later...
    strOrigValue = objConfig.GetOption(strOptionName)

    # Now set the value to our moniker...
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
    return os.path.expandvars(strConfigPath)

def main():
    if IsSessionReadOnly("Default"):
        crt.Dialog.MessageBox(
            "Your configuration folder/files seem to be read only.\r\n\r\n" +
            "Please ensure your user is able to create directories and " +
            "modify files in SecureCRT's configuration folder. \r\n\r\n")
        return

    global g_strConfigPath
    g_strConfigPath = GetConfigPath()

    # Select the keyword ini file to import
    strKeywordIniFilePath = crt.Dialog.FileOpenDialog(
        title="Select Keyword INI file to Import",
        filter="INI Files (*.ini)|*.ini||")
    if strKeywordIniFilePath == '':
        return

    strKeywordsFolder = os.path.join(g_strConfigPath, "Keywords")

    strKeywordsDestFileName = os.path.join(
        strKeywordsFolder,
        os.path.basename(strKeywordIniFilePath)
        )

    # In preparation for prompting the user in the case of a file collision
    # (where a file by that name already exists), find a unique file name
    # to use for this copy if the end user decides *not* to overwrite the
    # existing file.
    if os.path.isfile(strKeywordsDestFileName):
        nFileIndex = 1
        vFilenameTokens = os.path.splitext(os.path.basename(strKeywordIniFilePath))
        strFileBasename = vFilenameTokens[0]
        strFileExtension = vFilenameTokens[1]
        strNewUniqueFileName = ""
        while True:
            strNewUniqueFileName = os.path.join(
                strKeywordsFolder,
                "{0}-{1}{2}".format(
                    strFileBasename,
                    nFileIndex,
                    strFileExtension))
            if not os.path.isfile(strNewUniqueFileName):
                break
            nFileIndex += 1

        # Now, prompt the user if they desire to overwrite or use the
        # unique auto-generated name.
        BUTTON_YESNOCANCEL = 3
        nButtonClicked = crt.Dialog.MessageBox(
            "The {0}{1} Keywords file already exists in {2}.".format(
                strFileBasename,
                strFileExtension,
                strKeywordsFolder) +
                "\r\n\r\n" +
                "Yes:\tOverwrite the existing file\r\n\r\n"
                "No: \tSave it as '{0}'\r\n\r\n".format(
                   os.path.basename(strNewUniqueFileName)) +
                "Cancel:\tBail without further action.\r\n\r\n",
            "File Already Exists",
            BUTTON_YESNOCANCEL)
        if nButtonClicked == 2:
            # CANCEL
            return

        elif nButtonClicked == 6:
            # YES
            # This is a no-op since the copy function we'll be calling
            # will overwrite any existing file for us.
            strKeywordsDestFileName = strKeywordsDestFileName
        elif nButtonClicked == 7:
            # NO
            strKeywordsDestFileName = os.path.join(
                strKeywordsFolder,
                strNewUniqueFileName)

    # Create the Keywords folder if it does not already exist
    if not os.path.isdir(strKeywordsFolder):
        try:
            os.makedirs(strKeywordsFolder)
        except Exception as objInst:
            crt.Dialog.MessageBox(
                "Unable to create Keywords sub-folder in the SecureCRT " +
                "configuration path currently configured:\r\n\r\n" +
                strKeywordsFolder + "\r\n\r\nError:\r\n{0}".format(
                str(objInst)))
            return

    try:
        shutil.copy2(strKeywordIniFilePath, strKeywordsDestFileName)
    except Exception as objInst:
        crt.Dialog.MessageBox(
            "Failed to copy file...\r\n" +
            "from: {0}\r\n\r\nto: {1}\r\n\r\nError:\r\n{2}".format(
                strKeywordIniFilePath,
                strKeywordsDestFileName,
                str(objInst)))
        return

    # Check current sessions Keyword configuration
    objTab = crt.GetScriptTab()
    objConfig = objTab.Session.Config
    strKeyWordSet = objConfig.GetOption("Keyword Set")

    strKeywordsDestFileBasename = os.path.basename(strKeywordsDestFileName)
    strKeywordSetName = os.path.splitext(strKeywordsDestFileBasename)[0]

    if not strKeyWordSet == strKeywordSetName:
        strSetKeywordPrompt = (
            "This session ({0}) does not currently have the ".format(
                objTab.Session.Path) +
            "Keyword list set to '{0}'.\r\n".format(strKeywordSetName) +
            "\r\n" +
            "Would you like to enable the '{0}' ".format(strKeywordSetName) +
            "keyword list for the '{0}' session?".format(objTab.Session.Path))
        nButtonClicked = crt.Dialog.MessageBox(
            strSetKeywordPrompt,
            "Set Keword List?",
            ICON_QUESTION | BUTTON_YESNO)
        if nButtonClicked == IDNO:
            return
        objConfig.SetOption("Keyword Set", strKeywordSetName)
        objConfig.SetOption("Highlight Color", True)
        objConfig.SetOption("Highlight Bold", True)
        objConfig.SetOption("Highlight Reverse Video", False)


main()