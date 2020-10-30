#!/usr/bin/env python

"""
mapper is a module to apply a given command to all files (or directories) under a certain path.

Usage information is shown by running: ./mapper.py --help

mapper can be invoked directly or via map, which simply invokes this module.

More information is available at https://github.com/THLO/map.
"""

from __future__ import print_function
import os
import sys
import subprocess
import re
from map.map_argument_parser import MapArgumentParser
from map import map_constants as mc


class MapInputHandler(object):
    """
    MapInputHandler prepares the list of input files (or directories).
    The main method is

            getFiles(args),

    which creates and returns a list of the input files (or directories).
    """

    def get_directory_dictionary(self, args):
        """
        This function computes a dictionary containing
        all the directories that potentially contain (more) input.
        The returned dictionary 'table' indicates which of its contents are
        part of the input as follows:

        table[directory] == 'ALL' means that its entire content must be mapped
        table[directory] == 'ext' means that only content with the extension
            'ext' are mapped
        table[directory] == 'ext1,ext2' means that only content with either
            extension 'ext1' or 'ext2' are mapped

        Note that there is a special symbol
        map_constants.PLACEHOLDER_NO_EXTENSION_FILTER
        that enables the filtering for files without an extension.
        @param args: The parsed map arguments
        @return: A dictionary specifying what elements to map per directory
        """
        table = {}
        for element in args.path:
            # If the element is a directory, the dictionary entry is set
            # to 'ALL':
            if os.path.isdir(element):
                if element not in table:
                    table[element] = 'ALL'
            # If the element is a file, its extension is added to the
            # dictionary entry:
            else:
                path = os.path.dirname(element)
                extension = os.path.splitext(element)[1]
                # If there is no extension, a '.' was missing.
                # This happens when calling:
                # map -r [command] path/to/folder/*ext
                # and the folder 'folder' DOES NOT contain files with
                # the extension 'ext'.
                # In this case, there is no wildcard expansion and we must
                # create the proper extension manually:
                if extension == '':
                    extension = '.' + os.path.basename(element).split('*')[-1]
                if path not in table:
                    table[path] = extension
                elif table[path] != 'ALL' and extension not in table[path]:
                    table[path] = table[path] + "," + extension
        return table

    def create_list_recursively(self, args):
        """
        This is an internal method to create the list of input files
        (or directories) recursively, starting at the provided directory
        or directories.
        @param args: The parsed map arguments
        @return: List of map input files of directories
        """
        result_list = []
        directory_dict = self.get_directory_dictionary(args)
        for key in directory_dict:
            # Walk through the directory to find al	l input
            for path, directories, files in os.walk(key):
                for directory in directories:
                    result_list.append(os.path.join(path, directory))
                # Append the file if every file or the file's extension is
                # allowed to be mapped:
                for filename in files:
                    pattern = directory_dict[key].split(',')
                    if 'ALL' in pattern or \
                       os.path.splitext(filename)[1] in pattern:
                        result_list.append(os.path.join(path, filename))
        return list(set(result_list))

    def create_list(self, args):
        """
        This is an internal method to create the list of input files
        (or directories) contained in the provided directory or directories.
        @param args: The parsed map arguments
        @return: List of map input files of directories
        """
        result_list = []
        if len(args.path) == 1 and os.path.isdir(args.path[0]):
            result_list = [os.path.join(args.path[0], f)
                           for f in os.listdir(args.path[0])]
        else:
            # If there are multiple items, wildcard expansion has already
            # created the list of files.
            result_list = args.path
        return list(set(result_list))

    def get_extension_list(self, extensions):
        """
        This is an internal method that transforms the comma-separated
        extensions string into a list of extensions, e.g., "ext1,ext2,ext3"
        gets turned into ['.ext1','.ext2','.ext3'].
        If map_constants.PLACEHOLDER_NO_EXTENSION_FILTER is part of the string,
        the resulting list will also contain '', i.e., files without extensions
        are permitted.
        @param args: The parsed map arguments
        @return: List of extensions
        """
        basic_list = extensions.split(',')
        extension_list = []
        for ext in basic_list:
            if ext == mc.PLACEHOLDER_NO_EXTENSION_FILTER:
                # Files without an extension are permitted:
                extension_list.append('')
            elif ext != '':
                # The '.' is prepended if ext does not start with '.' already:
                ext_with_dot = ext if ext.startswith('.') else '.'+ext
                extension_list.append(ext_with_dot)
        return list(set(extension_list))

    def get_files(self, args):
        """
        This is the main method of the class. Given the arguments,
        the corresponding list of all files (or directories if the '-d'
        argument is used) are returned.
        @param args: The parsed map arguments
        @return: List of files or directories
        """
        file_list = []
        # The list is created by going through the folder(s) recursively:
        if args.recursive:
            file_list = self.create_list_recursively(args)
        else:    # The list is created by going through the provided folder(s):
            file_list = self.create_list(args)
        if args.directories:
            # If directories are returned, the list is sorted in reverse order.
            # This allows the processing of subfolders before the processing of
            # the parent folder.
            # Processing the parent folder first may not work because the
            # command may remove or rename the folder, which would affect
            # the subfolders.
            file_list = \
                [element for element in file_list if os.path.isdir(element)]
            return sorted(file_list, reverse=True)
        else:
            # Filter out all directories:
            file_list = \
                [element for element in file_list if os.path.isfile(element)]
            # Files are filtered based on their extensions:
            if args.extensions is not None:
                extension_list = self.get_extension_list(args.extensions)
                file_list = \
                    [element for element in file_list if
                     os.path.splitext(element)[1] in extension_list]
            # The files in the list are sorted in lexicographical order:
            return sorted(file_list)


class MapExecutor(object):
    """
    MapExecutor builds the command for each file (or directory) in a list.
    It further executes the set of commands.
    The commands are built by calling

        buildCommands(files)

    and the resulting commands are executed in succession by calling

        runCommands(commands)
    """

    def replace_in_commmand(self, command, pattern, replacement,
                            replacement_at_beginning):
        """
        This method replaces a certain 'pattern' in the provided command with a
        'replacement'.
        A different replacement can be specified when the pattern occurs right
        at the beginning of the command.
        @param command: The command
        @param pattern: The pattern
        @param replacement: The replacement for the pattern
        @param replacement_at_beginning: The replacement at the beginning
        @return: The updated command
        """
        # Turn the command into a list:
        command_list = list(command)
        # Get the indices of the pattern in the list:
        indices = [index.start() for index in re.finditer(pattern, command)]
        # Replace at the indices, unless the preceding character is the
        # escape character:
        for index in indices:
            if index == 0:
                command_list[index] = replacement_at_beginning
            elif command_list[index-1] != mc.ESCAPE_CHARACTER:
                command_list[index] = replacement
        # Put the pieces of the new command together:
        new_command = ''.join(command_list)
        # Remove superfluous slashes and return:
        return new_command.replace("//", "/")

    def escape_placeholders(self, input_string):
        """
        This method escapes all the placeholders defined in map_constants.py.
        @param input_string: The input string
        @return: The input with escaped placeholders
        """
        escape_char = mc.ESCAPE_CHARACTER
        escaped = input_string.replace(
            mc.PLACEHOLDER, escape_char + mc.PLACEHOLDER)
        escaped = escaped.replace(
            mc.PLACEHOLDER_FILENAME, escape_char + mc.PLACEHOLDER_FILENAME)
        escaped = escaped.replace(
            mc.PLACEHOLDER_PATH, escape_char + mc.PLACEHOLDER_PATH)
        escaped = escaped.replace(
            mc.PLACEHOLDER_EXTENSION, escape_char + mc.PLACEHOLDER_EXTENSION)
        escaped = escaped.replace(
            mc.PLACEHOLDER_COUNTER, escape_char + mc.PLACEHOLDER_COUNTER)
        return escaped

    def unescape_placeholders(self, input_string):
        """
        This method removes the escape characters.
        @param input_string: The input string
        @return: The input string without escape characters
        """
        return input_string.replace(mc.ESCAPE_CHARACTER, '')

    def build_part(self, command_part, filename_with_path, count, args):
        """
        This method builds a part of the command. It is used in the method
        build_command().
        @param command_part: Part of the command
        @param filename_with_path: Filename with path
        @param count: The current count
        @param args: The parsed map arguments
        @return: The built command part
        """
        # Get the path to the file:
        file_path = os.path.split(filename_with_path)[0]
        # Append '/' if there is a path, i.e., the file is not in the local
        # directory:
        if file_path != '':
            file_path += '/'
        # Get the file name without the path:
        filename_without_path = os.path.basename(filename_with_path)
        # Get the file name without the path and without the extension:
        plain_filename = os.path.splitext(filename_without_path)[0]
        # Get the extension:
        file_extension = os.path.splitext(filename_without_path)[1]

        # The original command part is retained:
        original_command_part = command_part

        # Replace the file placeholder character with the file:
        command_part = self.replace_in_commmand(
            command_part, mc.PLACEHOLDER, filename_without_path,
            filename_with_path)
        # Replace the path placeholder with the path:
        command_part = self.replace_in_commmand(
            command_part, mc.PLACEHOLDER_PATH, file_path, file_path)
        # Replace the plain file placeholder with the plain file:
        command_part = self.replace_in_commmand(
            command_part, mc.PLACEHOLDER_FILENAME, plain_filename,
            plain_filename)
        # Replace the extension placeholder with the extension:
        command_part = self.replace_in_commmand(
            command_part, mc.PLACEHOLDER_EXTENSION, file_extension,
            file_extension)
        # Replace the placeholder for the counter with the actual count:
        if args.number_length == 0:
            replacement_string = str(count)
        else:
            replacement_string = (
                '{0:0'+str(args.number_length)+'d}').format(count)
        command_part = self.replace_in_commmand(
            command_part, mc.PLACEHOLDER_COUNTER, replacement_string,
            replacement_string)
        # If the command part changed, it is put in quotes to avoid problems
        # with special characters:
        if original_command_part != command_part:
            command_part = '\"' + command_part + '\"'
        return command_part

    def build_command(self, filename, count, args):
        """
        This method builds the command for a particular file.
        @param filename: The input filename
        @param count: The current count
        @param args: The parsed map arguments
        @return: The built command
        """
        # Escape all placeholders in the file path:
        filename_with_path = self.escape_placeholders(filename)

        # The command is split into 'parts' separated by blank spaces:
        command_parts = args.command.split(' ')
        processed_parts = []
        # Each part of the command is processed separately:
        for part in command_parts:
            processed_parts.append(self.build_part(
                part, filename_with_path, count, args))
        # The parts are put together and the new command is returned:
        return self.unescape_placeholders(' '.join(processed_parts))

    def build_commands(self, files, args):
        """
        Given a list of (input) files, buildCommands builds all the commands.
        This is one of the two key methods of MapExecutor.
        @param files: The input files
        @param args: The parsed map arguments
        """
        commands = []
        count = args.count_from
        # For each file, a command is created:
        for filename in files:
            commands.append(self.build_command(filename, count, args))
            count += 1
        return commands

    def run_commands(self, commands, args):
        """
        Given a list of commands, this method executes them.
        This is one of the two key methods of MapExecutor.
        @param commands: The commands to be executed
        @param args: The parsed map arguments
        """
        error_counter = 0
        if args.list:
            print('\n'.join(commands))
        else:
            # Each command is executed sequentially:
            for command in commands:
                process = subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    shell=True)
                stream = process.communicate()
                output = stream[0]
                error_output = stream[1]
                return_code = process.returncode
                if args.verbose:
                    print('Executing command: '+command)
                if return_code != 0:
                    error_counter += 1
                    if args.verbose or not args.ignore_errors:
                        print('An error occurred:\n')
                        print(error_output)
                    if not args.ignore_errors:
                        print('Terminating map process.')
                        break
                if return_code == 0 and output:
                    sys.stdout.write(output.decode('utf-8'))
        if args.verbose:
            print('Process completed successfully.')
            if error_counter > 0:
                if error_counter > 1:
                    print(str(error_counter)
                          + ' errors occurred during the process.')
                else:
                    print(str(error_counter)
                          + ' error occurred during the process.')


class MapStarter(object):
    """ The MapStarter class is used to initiate the mapping process.
    It uses a MapArgumentParser instance to parse the input, a
    MapInputHandler to load the input that needs to be mapped, and then
    uses a MapExecutor instance to process the input.
    """

    def map(self):
        """ The method starts the mapping process.
        """
        # The argument parser is instantiated:
        parser = MapArgumentParser()

        # The arguments are parsed and returned:
        args = parser.parse_args()

        # The target files (or folders) are collected for the map job:
        if args.verbose:
            print('Collecting input for the map process...')
        input_handler = MapInputHandler()
        files = input_handler.get_files(args)

        # If there are no files (or folders), there is nothing to do:
        if not files:
            sys.stdout.write('No input for the map process found.\n')
            sys.exit(1)

        # If there is at least one file (or folder), create a MapExecutor:
        executor = MapExecutor()

        # Create the commands for the input files:
        commands = executor.build_commands(files, args)

        # Finally, the commands are executed sequentially:
        if args.verbose:
            print('Executing commands...')
        executor.run_commands(commands, args)


if __name__ == "__main__":
    # Create a MapStarter instance:
    MAPPER = MapStarter()
    # Start mapping:
    MAPPER.map()
