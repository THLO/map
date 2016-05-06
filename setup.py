from distutils.core import setup
import os

def getVersion():
    with open('version.py') as f: exec(f.read())
    return __version__

setup(name = "map",
    version = getVersion(),
    description = "map is a utility that applies a given command to all \
files/folders under a certain path.",
    author = "Thomas Locher",
    author_email = "thamasta@gmx.ch",
    url = "https://github.com/THLO/map",
    py_modules = ['mapper','MapArgumentParser','MapConstants','version'],
    scripts = ["map"],
    long_description = open('README.md').read(),
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
