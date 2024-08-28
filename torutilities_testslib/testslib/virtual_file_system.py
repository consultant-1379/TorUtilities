from io import BytesIO, FileIO, BufferedReader, BufferedWriter
import os


class VirtualFileSystem(object):
    """
    This is a helper class for mocking the builtin open method.
    It implements a virtual file system so that you can read/write data to the filesystem
    without actually modifying it
    Usage: @patch("__builtin__.open", VirtualFileSystem)
    Note: Virtual Files are persistant between test methods, If this is not the desired effect,
        add VirtualFileSystem.purge() to the setup method
    If data seems to persist even with the above added to the setup method, the file probably exists on the filesystem
    """

    _vfs = {}

    def __init__(self, name, mode='r'):
        self.mode = mode.replace('b', '')
        self.name = name

        # Ensure file exists if mode does not allow creating it
        if mode in ["r", "r+"] and name not in self._vfs and not os.path.exists(name):
            raise IOError("[Errno 2] No such file or directory: '{}'".format(name))

        if mode in ["w", "w+"]:
            contents = ""
        elif self.name in self._vfs:
            contents = self._vfs[self.name]
        elif os.path.exists(name):
            # Load data from filesystem into VFS
            file_on_disk = FileIO(name)
            contents = file_on_disk.read()
            file_on_disk.close()
        else:
            contents = ""

        self.contents = BytesIO(contents)

        # Make Virtual file readable/writable/both, depending on mode
        if self.mode in ["r"]:
            self._buffer = BufferedReader(self.contents, buffer_size=1)
        elif self.mode in ["w", "a"]:
            self._buffer = BufferedWriter(self.contents, buffer_size=1)
        elif self.mode in ["r+", "w+", "a+"]:
            self._buffer = self.contents
        else:
            raise ValueError("mode string must be one of 'r', 'r+', 'w', 'w+', 'a' or 'a+', not '{}'".format(self.mode))

        # Seek to position in stream
        if self.mode in ["w", "w+", "a", "a+"]:
            self._buffer.seek(len(self.contents.getvalue()))
        else:
            self._buffer.seek(0)

    def __getattr__(self, item):
        return getattr(self._buffer, item)

    def __iter__(self):
        return iter(self.contents)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        self._vfs[self.name] = self.contents.getvalue()

    @classmethod
    def purge(cls):
        cls._vfs = {}
