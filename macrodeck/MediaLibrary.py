import random
import os
from os.path import join as pathjoin  # aliasing so I don't confuse it with thread.join


# class to index music within a folder and its subfolders
class Library:
    def __init__(self, pdir):
        self.lib = {}
        self.nsongs = 0
        self.pdir = pdir  # parent dir
        self.key2ix = {}  # track index of each key for convenience

    def __getitem__(self, key):
        return self.lib[key]

    def __setitem__(self, key, value):
        self.lib[key] = value

    def finalize(self):
        # cleans up and indexes self.lib and calculates metadata
        # if Library is ever altered, this should run again

        empty = []
        self.index = []  # stores cumulative number of songs in each key
        i = 0  # not enumerating bc I want to skip empty dirs
        for key in self.lib.keys():
            if len(self.lib[key]) == 0:
                empty.append(key)
            else:
                self.nsongs += len(self.lib[key])
                self.index.append(self.nsongs)
                self.key2ix[key] = i
                i += 1

        for key in empty:
            self.lib.pop(key)

    def rsong(self):
        # returns a random song
        rint = random.randint(0, self.nsongs - 1)
        return self.song_from_index(rint)

    def song_from_index(self, ix):
        # returns song path from index
        # probably slow at scale
        for i, key in enumerate(self.lib.keys()):
            if ix < self.index[i]:
                if i == 0:
                    return pathjoin(
                        self.pdir, key, self.lib[key][ix]
                    )  # avoids index error below
                return pathjoin(self.pdir, key, self.lib[key][ix - self.index[i - 1]])

    def shuffle(self, dir=None):
        # generator function; returns shuffled song indices
        # if dir is specified, only returns indices from that dir

        if dir is None:
            start = 0
            end = self.nsongs
        else:
            start = 0 if self.key2ix[dir] == 0 else self.index[self.key2ix[dir] - 1]
            end = self.index[self.key2ix[dir]]

        playlist = list(range(start, end))
        random.shuffle(playlist)
        i = 0
        while i < len(playlist):
            yield self.song_from_index(playlist[i])
            i += 1


# helper functions


def index_library(path, lib=None, ignore=None):
    # parse music library, create list of songs
    # only checks for .mp3 files

    outer_loop = False

    if lib is None:
        lib = Library(path)
        path = ""
        outer_loop = True
    lib[path] = []

    for name in os.listdir(pathjoin(lib.pdir, path)):
        fullpath = pathjoin(path, name)
        if os.path.isdir(pathjoin(lib.pdir, fullpath)) and (
            ignore is None or name not in ignore
        ):  # recurse unless it should be ignored
            lib = index_library(fullpath, lib=lib, ignore=ignore)
        elif name[-3:].lower() == "mp3":
            lib[path].append(name)

    if outer_loop:
        lib.finalize()
    return lib
