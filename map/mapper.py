#!/usr/bin/env python

"""
mapper is a module to apply a given command to all files (or directories) under a certain path.

Usage information is shown by running: ./mapper.py --help

mapper can be invoked directly or via map, which simply invokes this module.

More information is available at https://github.com/THLO/map.
"""

import os,sys,argparse,subprocess,re
from MapArgumentParser import MapArgumentParser
import MapConstants

class MapInputHandler(object):
    """
    MapInputHandler prepares the list of input files (or directories).
    The main method is

            getFiles(args),

    which creates and returns a list of the input files (or directories).
    """

    def getDirectoryDictionary(self,args):
        """
        This is an internal method to compute a dictionary containing
        all the directories that potentially contain (more) input.
        The dictionary 'table' indicates which of its contents are part of the input:

        table[directory] == 'ALL' means that its entire content must be mapped
        table[directory] == 'ext' means that only content with the extension 'ext' are mapped
        table[directory] == 'ext1,ext2' means that only content with either extension 'ext1'
                            or 'ext2' are mapped

        Note that there is a special symbol MapConstants.placeholderNoExtensionFilter
        that enables the filtering for files without an extension.
        """
        table = {}
        for element in args.path:
            # If the element is a directory, the dictionary entry is set to 'ALL':
            if os.path.isdir(element):
                if element not in table:
                    table[element] = 'ALL'
            # If the element is a file, its extension is added to the dictionary entry:
            else:
                path = os.path.dirname(element)
                extension = os.path.splitext(element)[1]
                # If there is no extension, a '.' was missing. This happens when calling:
                # map -r [command] path/to/folder/*ext
                # and the folder 'folder' DOES NOT contain files with the extension 'ext'.
                # In this case, there is no wildcard expansion and we must create the
                # proper extension manually:
                if extension == '':
                    extension = '.' + os.path.basename(element).split("*")[-1]
                if path not in table:
                    table[path] = extension
                elif table[path] != 'ALL' and extension not in table[path]:
                    table[path] = table[path] + "," + extension
        return table

    def createListRecursively(self,args):
        """
        This is an internal method to create the list of input files (or directories)
        recursively, starting at the provided directory or directories.
        """
        resultList = []
        dirDict = self.getDirectoryDictionary(args)
        for key in dirDict:
            for path,dirs,files in os.walk(key):    # Walk through the directory to find al	l input
                for d in dirs:
                    resultList.append(os.path.join(path,d))
                for f in files:    # Append the file if 'ALL' are allowed or the extension is allowed
                        pattern = dirDict[key].split(',')
                        if 'ALL' in pattern or os.path.splitext(f)[1] in pattern:
                            resultList.append(os.path.join(path,f))
        return list(set(resultList))

    def createList(self,args):
        """
        This is an internal method to create the list of input files (or directories)
        contained in the provided directory or directories.
        """
        resultList = []
        if len(args.path) == 1 and os.path.isdir(args.path[0]):
            resultList = [os.path.join(args.path[0], f) for f in os.listdir(args.path[0])]
        else:    # If there are multiple items, wildcard expansion has already created the list of files
            resultList = args.path
        return list(set(resultList))

    def getExtensionList(self,extensions):
        """
        This is an internal method that transforms the comma-separated extensions string
        into a list of extensions, e.g., "ext1,ext2,ext3" gets turned into ['.ext1','.ext2','.ext3'].
        If MapConstants.placeholderNoExtensionFilter is part of the string, the resulting list
        will also contain '', i.e., files without extensions are permitted.
        """
        basicList = extensions.split(',')
        extensionList = []
        for ext in basicList:
            if ext == MapConstants.placeholderNoExtensionFilter:
                # Files without an extension are permitted:
                extensionList.append('')
            elif ext != '':
                # The '.' is prepended if ext does not start with '.' already:
                extWithDot = ext if ext.startswith('.') else '.'+ext
                extensionList.append(extWithDot)
        return list(set(extensionList))

    def getFiles(self,args):
        """
        This is the main method of the class. Given the arguments,
        the corresponding list of all files (or directories if the -d option is used)
        are returned.
        """
        fileList = []
        if args.recursive:    # The list is created by going through the folder(s) recursively:
            fileList = self.createListRecursively(args)
        else:    # The list is created by going through the provided folder(s):
            fileList = self.createList(args)
        if args.directories:
            # If directories are returned, the list is sorted in reverse order.
            # This allows the processing of subfolders before the processing of the parent folder.
            # Processing the parent folder first may not work because the command may remove
            # or rename the folder, which would affect the subfolders.
            fileList = [element for element in fileList if os.path.isdir(element)]
            return sorted(fileList,reverse=True)
        else:
            # Filter out all directories:
            fileList = [element for element in fileList if os.path.isfile(element)]
	    if args.extensions != None:    # Files are filtered based on their extensions:
                extensionList = self.getExtensionList(args.extensions)
                fileList = [element for element in fileList if os.path.splitext(element)[1] in extensionList]
            # The files in the list are sorted in lexicographical order:
            return sorted(fileList)

class MapExecutor(object):
    """
    MapExecutor builds the command for each file (or directory) in a list.
    It further executes the set of commands.
    The commands are built by calling

        buildCommands(files)
    
    and the resulting commands are executed in succession by calling

        runCommands(commands)
    """

    def replaceInCommand(self,command, pattern, replacement, replacementAtBeginning):
        """
        This is in internal method that replaces a certain 'pattern' in the
        provided command with a 'replacement'.
        A different replacement can be specified when the pattern occurs right
        at the beginning of the command.
        """
        # Turn the command into a list:
        commandAsList = list(command)
        # Get the indices of the pattern in the list:
        indices = [index.start() for index in re.finditer(pattern, command)]
        # Replace at the indices, unless the preceding character is the
        # escape character:
        for index in indices:
            if index == 0:
                commandAsList[index] = replacementAtBeginning
            elif commandAsList[index-1] != MapConstants.escape_char:
                commandAsList[index] = replacement
        # Put the pieces of the new command together:
        newCommand = ''.join(commandAsList)
        # Remove superfluous slashes and return:
        return newCommand.replace("//","/")
    
    def escapePlaceholders(self,inputString):
        """
        This is an internal method that escapes all the placeholders
        defined in MapConstants.py.
        """
        escaped = inputString.replace(MapConstants.placeholder,'\\'+MapConstants.placeholder)
        escaped = escaped.replace(MapConstants.placeholderFileName,'\\'+MapConstants.placeholderFileName)
        escaped = escaped.replace(MapConstants.placeholderPath,'\\'+MapConstants.placeholderPath)
        escaped = escaped.replace(MapConstants.placeholderExtension,'\\'+MapConstants.placeholderExtension)
        escaped = escaped.replace(MapConstants.placeholderCounter,'\\'+MapConstants.placeholderCounter)
        return escaped

    def unescapePlaceholders(self,inputString):
        """
        This is an internal method that removes the escape characters.
        """
        return inputString.replace('\\','')

    def buildPart(self,commandPart,fileNameWithPath,count,args):
        """
        This is in internal method that builds a part of the command,
        see buildCommand().
        """
        # Get the path to the file:
        filePath = os.path.split(fileNameWithPath)[0]
        # Append '/' if there is a path, i.e., the file is not in the local directory:
	if filePath != '':
            filePath = filePath +'/'
        # Get the file name without the path:
        fileNameWithoutPath = os.path.basename(fileNameWithPath)
        # Get the file name without the path and without the extension:
        plainFileName = os.path.splitext(fileNameWithoutPath)[0]
        # Get the extension:
        fileExtension = os.path.splitext(fileNameWithoutPath)[1]
        
        # The original command part is retained:
        originalCommandPart = commandPart

        # Replace the file placeholder character with the file:
        commandPart = self.replaceInCommand(commandPart,MapConstants.placeholder,fileNameWithoutPath,fileNameWithPath)
        # Replace the path placeholder with the path:
        commandPart = self.replaceInCommand(commandPart,MapConstants.placeholderPath,filePath,filePath)
        # Replace the plain file placeholder with the plain file:
        commandPart = self.replaceInCommand(commandPart,MapConstants.placeholderFileName,plainFileName,plainFileName)
        # Replace the extension placeholder with the extension:
        commandPart = self.replaceInCommand(commandPart,MapConstants.placeholderExtension,fileExtension,fileExtension)
        # Replace the placeholder for the counter with the actual count:
        if args.number_length == 0:
            replacementString = str(count)
        else:
            replacementString = ('{0:0'+str(args.number_length)+'d}').format(count)
        commandPart = self.replaceInCommand(commandPart,MapConstants.placeholderCounter,replacementString,replacementString)
        # If the command part changed, it is put in quotes to avoid problems with special characters:
        if originalCommandPart != commandPart:
            commandPart = '\"' + commandPart + '\"'
        return commandPart

    def buildCommand(self,fileName,count,args):
        """
        This is an internal method, building the command for a particular file.
        """
        # Escape all placeholders in the file path:
	fileNameWithPath = self.escapePlaceholders(fileName)

        # The command is split into 'parts', which are separated by blank spaces:
        commandParts = args.command.split(' ')
        processedParts = []
        # Each part of the command is processed separately:
        for part in commandParts:
            processedParts.append(self.buildPart(part,fileNameWithPath,count,args))
        # The parts are put together at the end and the new command is returned:
        return self.unescapePlaceholders(' '.join(processedParts))

    def buildCommands(self,files,args):
        """
        Given a list of (input) files, buildCommands builds all the commands.
        This is one of the two key methods of MapExecutor.
        """
        commands = []
        count = args.count_from
        # For each file, a command is created:
        for fileName in files:
            commands.append(self.buildCommand(fileName,count,args))
            count = count+1
        return commands

    def runCommands(self,commands,args):
        """
        Given a list of commands, runCommands executes them.
        This is one of the two key methods of MapExecutor.
        """
        errorCounter = 0
        if args.list:
            print '\n'.join(commands)
        else:
            # Each command is executed sequentially:
            for command in commands:
                process = subprocess.Popen(command, stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
                stream = process.communicate()
                output = stream[0]
                erroroutput = stream[1]
                returncode = process.returncode
                if args.verbose:
                    print 'Executing command: '+command
                if returncode != 0:
                    errorCounter = errorCounter + 1
                    if args.verbose or not args.ignore_errors:
                        print 'An error occurred:\n'
                        print erroroutput
                    if not args.ignore_errors:
                        print('Terminating map process.')
                        break
                if returncode == 0 and len(output) > 0:
                    sys.stdout.write(output)
        if args.verbose:
            print 'Process completed successfully.'
            if errorCounter > 0:
                if errorCounter > 1:
                    print str(errorCounter) + ' errors occurred during the process.'
                else:
                    print str(errorCounter) + ' error occurred during the process.'

# ***** This code is executed when running mapper.py: *****

class MapStarter(object):

    def map(self):
        # The argument parser is instantiated:
        parser = MapArgumentParser()

        # The arguments are parsed and returned:
        args = parser.parse_args()

        # The target files (or folders) are collected for the map job:
        if args.verbose:
            print 'Collecting input for the map process...'
        inputHandler = MapInputHandler()
        files = inputHandler.getFiles(args)

        # If there are no files (or folders), there is nothing to do:
        if len(files) == 0:
            sys.stdout.write('No input for the map process found.\n')
            sys.exit(1)

        # If there is at least one file (or folder), create a MapExecutor:
        executor = MapExecutor()

        # Create the commands for the input files:
        commands = executor.buildCommands(files,args)

        # Finally, the commands are executed sequentially:
        if args.verbose:
            print 'Executing commands...'
        executor.runCommands(commands,args)

if __name__ == "__main__":
    mapper = MapStarter()
    mapper.map()
