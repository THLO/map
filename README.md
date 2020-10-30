# map
`map` is a utility that offers a simple function in an easy-to-use manner:
A given command is applied to all files (or directories) under a certain path.

The same functionality can be achieved using `for` loops or `find -exec` or similar tools.
The advantage of `map` is that it is easier and more convenient to use.

## Usage
The basic usage is straightforward:
```
map [command] [path [path ...]]
```
`[command]` can be any shell command, but it must be in quotation marks.
`[path [path ...]]` is a path, or multiple paths, where the input files (or directories) are found for the shell command.
Wildcards (`*`) are allowed in the path(s).

The `[command]` can contain several placeholders that are substituted with the actual values before executing the command:

* `_` is used as the placeholder for the current file (or directory) including the full path.
* `&` is used as the placeholder for the path to the current file.
* `:` is used as the placeholder for the current file's name without its path or extension.
* `#` is used as the placeholder for the current file's extension including `.`.
* `%` is used to refer to an internal counter, incremented after each command.

For example, if the current file is `path/to/file/filename.ext` and this is the `9th` file that is being processed, then
* `_` is replaced by `path/to/file/filename.ext`.
* `&` is replaced by `path/to/file/`.
* `:` is replaced by `filename`.
* `#` is replaced by `.ext`.
* `%` is replaced by `8`.

`map` also provides several options:

* `-h, --help`:         show the help message and exit
* `-c, --count-from VALUE`:   set the internal counter to the provided start value
* `-d, --directories`:  apply the command to directories instead of files.
* `-i, --ignore-errors`: continue to execute commands even when a command has failed.
* `-l, --list`:          list all commands without executing them.
* `n LENGTH, --number-length LENGTH`:
                        format the counter that is used with `$`. The argument is the length
                        in terms of number of digits (with leading zeros).
* `-r, --recursive`:    search for files recursively under the provided path.
* `-v, --verbose`:      display detailed information about the process.
* `-V, --version`:      display information about the installed version.
* `-x EXT, --extensions EXT`:
                        apply the command to all files with any of the listed extensions.
                        The extensions must be provided in a comma-separated list.
                        By default, the command is applied to all files under the provided path.

## Examples
The following examples illustrate how to use `map`:

```
map "ls -la _" ~/Desktop
```
Detailed information about the files in the current user's `Desktop` folder is displayed.
Note that this command is equivalent to `ls -la ~/Desktop`.

```
map "mv _ /new/path/_" /old/path/
```
Move all the files under `/old/path/` to `/new/path/`.
Note that `map` is smart enough to drop the path when `_` is used as part of a path, i.e.,
`/new/path/_` is equivalent to `/new/path/-#` (concatenation of the file name and the extension).


```
map -r -x jpg,jpeg "jpegoptim _" ~/Pictures
```
Optimize all JPEG pictures found under `~/Pictures` including subdirectories
using [jpegoptim](https://github.com/tjko/jpegoptim).


```
map -rd "mv _ &/.." ~/Documents
```
Recursively move all directories under `Documents` up one level.

```
map -n 3 "mv _ &:-%#" ~/Documents/*.txt
```
Add a counter with three digits to the file names of all `txt` files, i.e,
`a.txt`, `b.txt` are renamed to `a-000.txt`, `b-001.txt` etc.

Note that `\` is the escape character for all placeholders, i.e., in order to write a regular underscore (`_`), write `\_`. The same principle applies to `:`, `&`, `#`, and `%`.

## Important Notes

Note that `map [command] /path/to/folder/*.txt` and `map -x txt [command] /path/to/folder/` are equivalent.
The `-x` option is useful when multiple extensions should be considered, e.g., `map -x jpg,jpeg,gif,png [command] /path/to/folder/`.
Further note that a command such as `map -x jpg [command] /path/to/folder/*.jpeg` returns

```
No input for the map process found.
```

The reason is that only files with the extension `jpeg` are considered under the provided path.
It will then filter out all files that do not have the extension `jpg`, resulting in an empty input.

The commands `map [command] /path/to/folder` and `map [command] /path/to/folder/*` provide the same output.
The same is true when using the option `-r, --recursive`.

However, while `map -r [command] /path/to/folder /path/to/anotherfolder` correctly executes `[command]` for all
files found under either `/path/to/folder` or `/path/to/anotherfolder`, the same command without `-r, --recursive`, i.e.,
`map [command] /path/to/folder /path/to/anotherfolder` returns

```
No input for the map process found.
```
The reason is that the command is indistinguishable from `map [command] /path/to/*` when the folder `to` contains
only the two subfolders `folder` and `subfolder`. In this case, since there are no files under `/path/to`, there is
no input for the map process.
Therefore, for the sake of consistency, the command `map [command] /path/to/folder /path/to/anotherfolder` also does not
map anything.
In order to execute the command for all files in both folders, wildcard expansion can be used:
```
map [command] /path/to/folder/* /path/to/anotherfolder/*
```

## Installation

There are multiple installation options.
The first two options are preferable because they offer a simple update mechanisms.

1) If you are running Ubuntu, you can install `map` by first adding the `PPA` as follows:

```
sudo add-apt-repository ppa:thamasta/thlo-utils
```

Next, run `sudo apt-get update` followed by

```
sudo apt-get install map
```

2) If you have `Python` installed, `map` can be downloaded from [PyPI](https://pypi.python.org/) using `pip` as follows:
```
sudo pip install map
```
Note that running the same command with `-U` appended updates `map` to the latest version.

It is also possible to install `map` manually, as the following options show.

3) If you are running any operating system that uses `deb` packages, download the file `map_[version number].deb` in the folder `installation`
and then run

```
dpkg -i map_[version number].deb
```

4) If you have `Python` installed, you can install `map`
by downloading `map-[verson number].tar.gz` and `install_tar` in the folder `installation`.
You can verify the integrity of the tarball by downloading `MD5_CHECKSUMS`, running `md5sum`, and comparing the computed hash against the hash in `MD5_CHECKSUMS`.

Next, install `map` by simply invoking the installation script `install_tar`.
Note that the installation requires super user rights.
In order to remove `map`, simply download `uninstall_tar` and run it.

### Old Releases

You can download tarballs of old releases by navigating to the website
`https://github.com/THLO/map/tarball/[version number]`, where `[version number]` must be replaced by the desired version. The format is `v.X.Y.Z`, e.g., `v.1.0.0`.
Note that these tarballs contain the entire project and therefore the hashes will not match the MD5 checksums in the file `MD5_CHECKSUMS` under `installation`.
