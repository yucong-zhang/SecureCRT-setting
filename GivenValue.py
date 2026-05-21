#$language = "Python"
#$interface = "1.0"

# SetColorScheme(simple).py
#   Last Modified: 02 Feb, 2016
#     - Initial conversion of VBScript version to Python
#
# Description:
#   - Shows how to set color scheme via a script.
#
# Usage:
#   - Save script to your computer
#   - Map a button on the SecureCRT Button Bar to run
#     this script.
#       --> In the Arguments field, put the name of the
#           color scheme you desire to switch to. Note
#           that if the name of the color scheme you
#           specify doesn't actually exist, there is
#           no error returned.

if crt.Arguments.Count > 0:
    bANSIColor = crt.Session.Config.GetOption("ANSI Color")
    if bANSIColor:
        crt.Session.Config.SetOption("Color Scheme Overrides Ansi Color", True)
    
    strArg = crt.Arguments.GetArg(0)
    
    # Safe programming... what if the individual set arg to a color
    # scheme that has spaces, but forgot to enclose it in double quotes?
    if crt.Arguments.Count > 1: 
        for i in range(1,crt.Arguments.Count):
            strArg = strArg + " " + crt.Arguments.GetArg(i)
            
    crt.Session.Config.SetOption("Color Scheme", strArg)
    crt.Session.SetStatusText(strArg)
else:
    crt.Dialog.MessageBox("Scheme name must be specified as script argument.")