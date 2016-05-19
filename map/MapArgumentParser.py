"""
MapARgumentParser extends the standard ArgumentParser for map.
It defines all arguments for map.

Information about map is available at https://github.com/THLO/map.
"""

import argparse,os
from argparse import ArgumentParser
import MapConstants

class MapArgumentParser(ArgumentParser):

    def __init__(self):
        super(MapArgumentParser,self).__init__(description="The given command is applied to all \
files/directories under the provided path.\n\
The command must be set in quotation marks.\n\n\
placeholders:\n  \
"+MapConstants.placeholder+" is used as the placeholder for the current matching file including the full path.\n  \
"+MapConstants.placeholderFileName+" is used as the placeholder for the current file's name without its path or extension.\n  \
"+MapConstants.placeholderPath+" is used as the placeholder for the current file's path.\n  \
"+MapConstants.placeholderExtension+" is used as the placeholder for the current file's extension including the dot.\n  \
"+MapConstants.placeholderCounterHelpVersion+" is used to refer to an internal counter,\
incremented after each command.\n\n\
examples:\n  map \"mv " + MapConstants.placeholder + " " + MapConstants.placeholderPath +
MapConstants.placeholderFileName + MapConstants.placeholderCounterHelpVersion + MapConstants.placeholderExtension +
"\" /path/to/folder: A counter is added to all file names.\n" \
"  map -r \"mv "+MapConstants.placeholder + " " + MapConstants.placeholderPath + "/..\" /path/to/folder: \
Each file is moved to its respective parent directory.",formatter_class=argparse.RawDescriptionHelpFormatter)
        # Get the version information:
        info = loadVersionInfo()
	version = info['__version__']
        versionText = info['__version_text__']
        # Add all arguments:
	# Get a group for the mutually exclusive options '-x' and '-d':
	groupXD = self.add_mutually_exclusive_group()
        self.add_argument("-c", "--count-from", type=checkNegative,default=0,help="set the internal counter to the provided start value.")
        # It is not allowed to use the extension option (-x) with the directories option (-d)
        groupXD.add_argument("-d", "--directories", action="store_true",help="apply the command to directories instead of files.")
        self.add_argument("-i", "--ignore-errors", action="store_true", help="continue to execute commands even when a command has failed.")
        self.add_argument("-l", "--list", action="store_true", help="list all commands without executing them.")
        self.add_argument("-n", "--number-length", type=checkNegative,default=0,help="format the counter that is used with \
"+MapConstants.placeholderCounterHelpVersion+". The argument is the length in terms of number of digits of the counter (with leading zeros).")
        self.add_argument("-r", "--recursive", action="store_true",help="search for files recursively under the provided path.")
        self.add_argument("-v", "--verbose", action="store_true", help="display detailed information about the process.")
        self.add_argument("-V",'--version', action='version', version='map '+version+'\n'+versionText,help="display information about the installed version.")
        groupXD.add_argument("-x", "--extensions", help="apply the command to all files with any of the listed extensions.\
 The extensions must be provided in a comma-separated list. By default, the command is \
applied to all files under the provided path. The symbol '"+MapConstants.placeholderNoExtensionFilter+"' is used to\
 filter for files without an extension.")
        self.add_argument("command", help="The command that is applied to all matching files/directories.")
        self.add_argument("path",nargs='*', help="The (top-level) path where matching files are sought.")

    def format_help(self):
        """ The help statement is slightly changed in that:
        1) MapConstants.placeholderCounterHelpVersion is replaced MapConstants.placeholderCounter
        2) 'COUNT_FROM', 'NUMBER_LENGTH', and 'EXTENSIONS' are shortened to 'VALUE', 'LENGTH', and 'EXT', respectively.
        """
	return super(MapArgumentParser,self).format_help().replace(MapConstants.placeholderCounterHelpVersion,MapConstants.placeholderCounter).replace('COUNT_FROM','VALUE').replace('NUMBER_LENGTH','LENGTH').replace('EXTENSIONS','EXT')

def checkNegative(value):
    errorMessage = "%s is invalid because only non-negative integers are allowed." % value
    try: 
        intvalue = int(value)
        if intvalue < 0:
            raise argparse.ArgumentTypeError(errorMessage)
    except ValueError:
        raise argparse.ArgumentTypeError(errorMessage)
    return intvalue

def loadVersionInfo():
    directory = os.path.dirname(__file__)
    ns = {}
    with open(os.path.join(directory,'version.py')) as f: exec(f.read(),ns)
    return ns    
