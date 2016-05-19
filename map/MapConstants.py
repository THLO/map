"""
MapConstants defines constants used by map.

Information about map is available at https://github.com/THLO/map.
"""

# These are the main placeholders used by map:

placeholder = '_'
placeholderFileName = ':'
placeholderPath = '&'
placeholderExtension = '#'
placeholderCounter = '%'

# Since any single '%' character is interpreted as the start of an
# argument specifier, we need '%%' for the help text:

placeholderCounterHelpVersion = '%%'

# The standard escape character is used:

escape_char = '\\'

# The following placeholder is used to filter for files without
# extensions:

placeholderNoExtensionFilter = '^' 
