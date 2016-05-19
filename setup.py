try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
 
import os

def getVersion():
    with open(os.path.join(os.path.dirname(__file__),'map/version.py')) as f: exec(f.read())
    return __version__

setup(name = "map",
    version = getVersion(),
    description = "map applies a command to files/folders at a certain path.",
    author = "Thomas Locher",
    author_email = "thamasta@gmx.ch",
    url = "https://github.com/THLO/map",
    download_url = "https://github.com/THLO/map/tarball/v."+getVersion(),
    packages = ['map'],
    scripts = ['map/map'],
    long_description = "The same functionality to apply a command to multiple files/folders\n\
can be achieved using for loops or find -exec or similar tools.\n\
The advantage of map is that it is easier and more convenient to use.\n\
More information on map can be found at https://github.com/THLO/map or by running map --help.",
    license = 'GNU General Public License v3 (GPLv3)',
    platforms = 'POSIX',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Desktop Environment',
      ]
) 
