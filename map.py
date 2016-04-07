#!/usr/bin/env python

"""
map applies a given command to all files (or directories) under a certain path.

Usage information is shown by running: ./map.py --help

More information is available at https://github.com/THLO/map.
"""


import os,sys,argparse,subprocess,re
from MapArgumentParser import MapArgumentParser

"""
The following symbols have special meanings in a map command:
"""
placeholder = '_'
placeholderFileName = '-'
placeholderPath = '&'
placeholderExtension = '#'
placeholderCounter = '%'
"""
Since any single '%' character is interpreted as the start of an
argument specifier, we need '%%' for the help text:
"""
placeholderCounterHelpVersion = '%%'
escape_char = '\\'

version_text = 'Copyright (C) 2016 Thomas Locher\n \
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.\n \
This is free software: you are free to change and redistribute it.\n \
There is NO WARRANTY, to the extent permitted by law.\n\n \
Written by Thomas Locher'

def getDirectoryDictionary():
    table = {}
    for element in args.path:
        if os.path.isdir(element):
            if element not in table:
                table[element] = 'ALL'
        else:
            path = os.path.dirname(element)
            extension = os.path.splitext(element)[1]
            if extension == '':
                extension = '.' + os.path.basename(element).split("*")[-1]
            if path not in table:
                table[path] = extension
            elif table[path] != 'ALL' and extension not in table[path]:
                table[path] = table[path] + "," + extension
    return table

def createListRecursively():
    resultList = []
    dirDict = getDirectoryDictionary()
    for key in dirDict:
        for path,dirs,files in os.walk(key):
            for d in dirs:
                resultList.append(os.path.join(path,d))
            for f in files:
                    if dirDict[key] == 'ALL' or os.path.splitext(f)[1] in dirDict[key]:
                        resultList.append(os.path.join(path,f))
    return list(set(resultList))

def createList():
    resultList = []
    if len(args.path) == 1 and os.path.isdir(args.path[0]):
        resultList = [os.path.join(args.path[0], f) for f in os.listdir(args.path[0])]
    else:    # If there are multiple items, wildcard expansion has already created the list of files
        resultList = args.path
    return list(set(resultList))

def findFiles():
    list = []
    if args.recursive:
        list = createListRecursively()
    else:
        list = createList()
    if args.directories:
        list = [element for element in list if os.path.isdir(element)]
        return sorted(list,reverse=True)
    else:
        list = [element for element in list if os.path.isfile(element)]
        return sorted(list)


def replaceInCommand(command, pattern, replacement, replacementAtBeginning):
    commandAsList = list(command)
    indices = [index.start() for index in re.finditer(pattern, command)]
    for index in indices:
        if index == 0:
            commandAsList[index] = replacementAtBeginning
        elif commandAsList[index-1] != escape_char:
            commandAsList[index] = replacement
        else:
            commandAsList[index-1] = ''
    newCommand = ''.join(commandAsList)
    # Remove superfluous slashes and return:
    return newCommand.replace("//","/")

def buildPart(commandPart,fileName,count):
    fileNameWithPath = fileName.replace(' ','\\ ')
    filePath = os.path.split(fileNameWithPath)[0]+'/'
    fileNameWithoutPath = os.path.basename(fileName)
    plainFileName = os.path.splitext(fileNameWithoutPath)[0].replace(' ','\\ ')
    fileExtension = os.path.splitext(fileNameWithoutPath)[1]
    # Replace the file placeholder character with the file:
    commandPart = replaceInCommand(commandPart,placeholder,fileNameWithoutPath,fileNameWithPath)
    # Replace the path placeholder with the path:
    commandPart = replaceInCommand(commandPart,placeholderPath,filePath,filePath)
    # Replace the plain file placeholder with the plain file:
    commandPart = replaceInCommand(commandPart,placeholderFileName,plainFileName,plainFileName)
    # Replace the extension placeholder with the extension:
    commandPart = replaceInCommand(commandPart,placeholderExtension,fileExtension,fileExtension)
    # Replace the placeholder for the counter with the actual count:
    if args.number_length == 0:
        replacementString = str(count)
    else:
        replacementString = ('{0:0'+str(args.number_length)+'d}').format(count)
    commandPart = replaceInCommand(commandPart,placeholderCounter,replacementString,replacementString)
    
    return commandPart

def buildCommand(fileName,count):
    commandParts = args.command.split(' ')
    processedParts = []
    for part in commandParts:
        processedParts.append(buildPart(part,fileName,count))
    return ' '.join(processedParts)

def buildCommands(files):
    commands = []
    count = 0
    for fileName in files:
        commands.append(buildCommand(fileName,count))
        count = count+1
    return commands

def runCommands(commands):
    errorCounter = 0
    if args.list:
        print '\n'.join(commands)
    else:
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

old_dir = os.getcwd()
os.chdir(os.path.dirname(__file__))
execfile('version.py')
os.chdir(old_dir)
version = __version__

parser = MapArgumentParser(description="The given command is applied to all \
files/directories under the provided path.\n\
The command must be set in quotation marks.\n\n\
placeholders:\n  \
"+placeholder+" is used as the placeholder for the current matching file including the full path.\n  \
"+placeholderFileName+" is used as the placeholder for the current file's name without its path or extension.\n  \
"+placeholderPath+" is used as the placeholder for the current file's path.\n  \
"+placeholderExtension+" is used as the placeholder for the current file's extension including the dot.\n  \
"+placeholderCounterHelpVersion+" is used to refer to an internal counter,\
incremented after each command.\n\n\
examples:\n  map \"mv _ &-%#\" /path/to/folder: A counter is added to all file names.\n" \
"  map -r \"mv _ &/..\" /path/to/folder: Each file is moved to its respective parent directory.",formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("-c", "--count-from", type=int,default=0,help="set the internal counter to the provided start value. [NOT YET IMPLEMENTED]")
parser.add_argument("-d", "--directories", action="store_true",help="apply the command to directories instead of files.")
parser.add_argument("-i", "--ignore-errors", action="store_true", help="continue to execute commands even when a command has failed.")
parser.add_argument("-l", "--list", action="store_true", help="list all commands without executing them.")
parser.add_argument("-n", "--number-length", type=int,default=0,help="format the counter that is used with \
"+placeholderCounterHelpVersion+". The argument is the length in terms of number of digits of the counter (with leading zeros).")
parser.add_argument("-r", "--recursive", action="store_true",help="search for files recursively under the provided path.")
parser.add_argument("-v", "--verbose", action="store_true", help="display detailed information about the process.")
parser.add_argument("-V",'--version', action='version', version='map '+version+'\n'+version_text,help="display information about the installed version.")
parser.add_argument("-x", "--extensions", help="apply the command to all files with any of the listed extensions. The extensions must be provided in a comma-separated list. By default, the command is \
applied to all files under the provided path. [NOT YET IMPLEMENTED]")

parser.add_argument("command", help="The command that is applied to all matching files/directories.")
parser.add_argument("path",nargs='*', help="The (top-level) path where matching files are sought.")

args = parser.parse_args()

if args.verbose:
    print 'Collecting input for the map process...'
files = findFiles()

if len(files) == 0:
    sys.stdout.write('No input for the map process found.\n')
    sys.exit(1)

commands = buildCommands(files)

if args.verbose:
    print 'Executing commands...'
runCommands(commands)
