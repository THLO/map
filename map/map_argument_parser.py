"""
MapARgumentParser extends the standard ArgumentParser for map.
It defines all arguments for map.

Information about map is available at https://github.com/THLO/map.
"""

import os
import argparse
from argparse import ArgumentParser
from map import map_constants as mc


class MapArgumentParser(ArgumentParser):
    """ MapArgumentParser parses the arguments when invoking map.
    """

    def __init__(self):
        """ The constructor creates a MapArgumentParser object."""
        description_string = "The given command is applied to all " \
        "files/directories under the provided path.\nThe command must be set " \
        "in quotation marks.\n\nplaceholders:\n"+mc.PLACEHOLDER+ \
        " is used as the placeholder for the current matching file including " \
        "the full path.\n"+mc.PLACEHOLDER_FILENAME+" is used as the " \
        "placeholder for the current file's name without its path or " \
        "extension.\n"+mc.PLACEHOLDER_PATH+" is used as the " \
        "placeholder for the current file's path.\n"+ \
        mc.PLACEHOLDER_EXTENSION+" is used as the placeholder for " \
        "the current file's extension including the dot.\n" + \
        mc.PLACEHOLDER_COUNTER_HELP_TEXT+" is used to refer to " \
        "an internal counter, incremented after each command.\n\n" \
        "Examples:\n  map \"mv " + mc.PLACEHOLDER + " " + \
        mc.PLACEHOLDER_PATH + mc.PLACEHOLDER_FILENAME + \
        mc.PLACEHOLDER_COUNTER_HELP_TEXT + \
        mc.PLACEHOLDER_EXTENSION + "\" /path/to/folder: A counter " \
        "is added to all file names.\n  map -r \"mv "+ \
        mc.PLACEHOLDER + " " + mc.PLACEHOLDER_PATH + \
        "/..\" /path/to/folder: Each file is moved to its respective " \
        "parent directory."
        super(MapArgumentParser, self).__init__(
            description=description_string, formatter_class=\
            argparse.RawDescriptionHelpFormatter)
        # Get the version information:
        info = get_version_info()
        # Extract the version number:
        version = info['__version__']
        # Extract the version text:
        version_text = info['__version_text__']
        # Add all arguments:
        # Get a group for the mutually exclusive options '-x' and '-d':
        group_xd = self.add_mutually_exclusive_group()
        # Add the argument "-c" to set the counter:
        self.add_argument("-c", "--count-from", type=check_negative, default=0,\
            help="set the internal counter to the provided start value.")
        # It is not allowed to use the extension option (-x) with
        # the directories option (-d):
        group_xd.add_argument("-d", "--directories", action="store_true", \
            help="apply the command to directories instead of files.")
        group_xd.add_argument("-x", "--extensions", help="apply the command to \
            all files with any of the listed extensions. The extensions must \
            be provided in a comma-separated list. By default, the command is \
            applied to all files under the provided path. The symbol '" + \
            mc.PLACEHOLDER_NO_EXTENSION_FILTER+"' is used to filter for \
            files without an extension.")
        # Add the argument "-i" to ignore errors:
        self.add_argument("-i", "--ignore-errors", action="store_true", \
            help="continue to execute commands even when a command has failed.")
        # Add the argument "-l" to list commands without executing them:
        self.add_argument("-l", "--list", action="store_true", \
            help="list all commands without executing them.")
        # Add the argument "-n" to specify the number of digits for the counter:
        self.add_argument("-n", "--number-length", type=check_negative, \
            default=0, help="format the counter that is used with " + \
            mc.PLACEHOLDER_COUNTER_HELP_TEXT+". The argument is \
            the length in terms of number of digits of the counter (with \
            leading zeros).")
        # Add the argument "-r" to search recursively:
        self.add_argument("-r", "--recursive", action="store_true", \
            help="search for files recursively under the provided path.")
        # Add the argument "-v" for verbose output:
        self.add_argument("-v", "--verbose", action="store_true", \
            help="display detailed information about the process.")
        # Add the argument "-V" to print the version:
        self.add_argument("-V", '--version', action='version', version='map '+ \
            version +'\n'+version_text, help="display information about the \
            installed version.")
        # Add the mandatory command argument:
        self.add_argument("command", help="The command that is applied to all \
            matching files/directories.")
        # Add the mandatory path argument:
        self.add_argument("path", nargs='*', help="The (top-level) path where \
            matching files are sought.")

    def format_help(self):
        """ The help statement is slightly changed in that
        1) map_constants.placeholderCounterHelpVersion is replaced by
        map_constants.PLACEHOLDER_COUNTER
        2) 'COUNT_FROM', 'NUMBER_LENGTH', and 'EXTENSIONS' are shortened to
        'VALUE', 'LENGTH', and 'EXT', respectively.
        @return: The formatted help text
        """
        return super(MapArgumentParser, self).format_help().replace(
            mc.PLACEHOLDER_COUNTER_HELP_TEXT,
            mc.PLACEHOLDER_COUNTER).replace('COUNT_FROM', \
            'VALUE').replace('NUMBER_LENGTH', 'LENGTH').replace('EXTENSIONS', \
            'EXT')

def check_negative(value):
    """ The method checks if the provided value is negative.
    @param value: The input value in the form of a string
    @return: The integer value of the input
    """
    error_message = value + "is invalid because only non-negative integers are \
        allowed."
    # Try to convert the value to an integer:
    try:
        int_value = int(value)
        # An error is raised if the value is negative:
        if int_value < 0:
            raise argparse.ArgumentTypeError(error_message)
    except ValueError:
        raise argparse.ArgumentTypeError(error_message)
    # Return the integer value:
    return int_value


def get_version_info():
    """ The method returns the version information.
    @return: The dictionary containing the version information
    """
    directory = os.path.dirname(__file__)
    # The dictionary containing the version information:
    version_dict = {}
    # Populate the dictionary using the content of the file 'version.py':
    with open(os.path.join(directory, 'version.py')) as version_file:
        # pylint: disable=exec-used
        exec(version_file.read(), version_dict)
    # Return the version dictionary:
    return version_dict
