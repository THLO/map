"""
map_constants defines constants used by map.

Information about map is available at https://github.com/THLO/map.
"""

# These are the main placeholders used by map:

PLACEHOLDER = '_'
PLACEHOLDER_FILENAME = ':'
PLACEHOLDER_PATH = '&'
PLACEHOLDER_EXTENSION = '#'
PLACEHOLDER_COUNTER = '%'

# Since any single '%' character is interpreted as the start of an
# argument specifier, we need '%%' for the help text:

PLACEHOLDER_COUNTER_HELP_TEXT = '%%'

# The standard escape character is used:

ESCAPE_CHARACTER = '\\'

# The following placeholder is used to filter for files without
# extensions:

PLACEHOLDER_NO_EXTENSION_FILTER = '^'
