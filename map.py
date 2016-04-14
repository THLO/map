#!/usr/bin/env python

"""
map applies a given command to all files (or directories) under a certain path.

Usage information is shown by running: ./map.py --help

More information is available at https://github.com/THLO/map.
"""


import os,sys,argparse,subprocess,re
from MapArgumentParser import MapArgumentParser
import MapConstants

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

def matchesExtension(input, extensions):
    extensionList = extensions.split(',')
    extensionListWithDot = []
    for ext in extensionList:
        next = ext if ext.startswith('.') else '.'+ext
        extensionListWithDot.append(next)
    return os.path.splitext(input)[1] in extensionListWithDot

def findFiles():
    fileList = []
    if args.recursive:
        fileList = createListRecursively()
    else:
        fileList = createList()
    if args.directories:
        fileList = [element for element in fileList if os.path.isdir(element)]
        return sorted(list,reverse=True)
    else:
        fileList = [element for element in fileList if os.path.isfile(element)]
	if args.extensions != None:
            fileList = [element for element in fileList if matchesExtension(element,args.extensions)]
        return sorted(fileList)


def replaceInCommand(command, pattern, replacement, replacementAtBeginning):
    commandAsList = list(command)
    indices = [index.start() for index in re.finditer(pattern, command)]
    for index in indices:
        if index == 0:
            commandAsList[index] = replacementAtBeginning
        elif commandAsList[index-1] != MapConstants.escape_char:
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
    commandPart = replaceInCommand(commandPart,MapConstants.placeholder,fileNameWithoutPath,fileNameWithPath)
    # Replace the path placeholder with the path:
    commandPart = replaceInCommand(commandPart,MapConstants.placeholderPath,filePath,filePath)
    # Replace the plain file placeholder with the plain file:
    commandPart = replaceInCommand(commandPart,MapConstants.placeholderFileName,plainFileName,plainFileName)
    # Replace the extension placeholder with the extension:
    commandPart = replaceInCommand(commandPart,MapConstants.placeholderExtension,fileExtension,fileExtension)
    # Replace the placeholder for the counter with the actual count:
    if args.number_length == 0:
        replacementString = str(count)
    else:
        replacementString = ('{0:0'+str(args.number_length)+'d}').format(count)
    commandPart = replaceInCommand(commandPart,MapConstants.placeholderCounter,replacementString,replacementString)
    
    return commandPart

def buildCommand(fileName,count):
    commandParts = args.command.split(' ')
    processedParts = []
    for part in commandParts:
        processedParts.append(buildPart(part,fileName,count))
    return ' '.join(processedParts)

def buildCommands(files):
    commands = []
    count = args.count_from
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

# ***** This code is executed when running map.py: *****

# The argument parser is instantiated:
parser = MapArgumentParser()

# The arguments are parsed and returned:
args = parser.parse_args()

# The target files (or folders) are collected for the map job:
if args.verbose:
    print 'Collecting input for the map process...'
files = findFiles()

# If there are no files (or folders), there is nothing to do:
if len(files) == 0:
    sys.stdout.write('No input for the map process found.\n')
    sys.exit(1)

# If there is at least one file (or folder), the commands are built:
commands = buildCommands(files)

# Finally, the commands are executed sequentially:
if args.verbose:
    print 'Executing commands...'
runCommands(commands)
