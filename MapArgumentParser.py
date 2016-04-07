"""
MapARgumentParser extends the standard ArgumentParser for map.py.

Information about map is available at https://github.com/THLO/map.
"""

from argparse import ArgumentParser

class MapArgumentParser(ArgumentParser):

    def format_help(self):
        """ The help statement is slightly changed in that the '.py' extension is dropped. """
	return super(MapArgumentParser,self).format_help().replace('.py','').replace('%%','%')
	


