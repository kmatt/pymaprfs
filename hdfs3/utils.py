
from contextlib import contextmanager
import os
import shutil
import tempfile


def seek_delimiter(file, delimiter, blocksize):
    """ Seek current file to next byte after a delimiter bytestring

    This seeks the file to the next byte following the delimiter.  It does
    not return anything.  Use ``file.tell()`` to see location afterwards.

    Parameters
    ----------
    file: a file
    delimiter: bytes
        a delimiter like ``b'\n'`` or message sentinel
    blocksize: int
        Number of bytes to read from the file at once.
    """

    if file.tell() == 0:
        return

    last = b''
    while True:
        current = file.read(blocksize)
        if not current:
            return
        full = last + current
        try:
            i = full.index(delimiter)
            file.seek(file.tell() - (len(full) - i) + len(delimiter))
            return
        except ValueError:
            pass
        last = full[-len(delimiter):]


def read_block(f, offset, length, delimiter=None):
    """ Read a block of bytes from a file

    Parameters
    ----------
    fn: string
        Path to filename on HDFS
    offset: int
        Byte offset to start read
    length: int
        Number of bytes to read
    delimiter: bytes (optional)
        Ensure reading starts and stops at delimiter bytestring

    If using the ``delimiter=`` keyword argument we ensure that the read
    starts and stops at delimiter boundaries that follow the locations
    ``offset`` and ``offset + length``.  If ``offset`` is zero then we
    start at zero.  The bytestring returned will not include the
    surrounding delimiter strings.

    Examples
    --------

    >>> from io import BytesIO  # doctest: +SKIP
    >>> f = BytesIO(b'Alice, 100\\nBob, 200\\nCharlie, 300')  # doctest: +SKIP
    >>> read_block(f, 0, 13)  # doctest: +SKIP
    b'Alice, 100\\nBo'

    >>> read_block(f, 0, 13, delimiter=b'\\n')  # doctest: +SKIP
    b'Alice, 100\\nBob, 200'

    >>> read_block(f, 10, 10, delimiter=b'\\n')  # doctest: +SKIP
    b'Bob, 200\\nCharlie, 300'
    """
    if delimiter:
        f.seek(offset)
        seek_delimiter(f, delimiter, 2**16)
        start = f.tell()
        length -= start - offset

        f.seek(start + length)
        seek_delimiter(f, delimiter, 2**16)
        end = f.tell()
        eof = not f.read(1)

        offset = start
        length = end - start

        if length and not eof:
            length -= len(delimiter)

    f.seek(offset)
    bytes = f.read(length)
    return bytes


@contextmanager
def tmpfile(extension=''):
    extension = '.' + extension.lstrip('.')
    handle, filename = tempfile.mkstemp(extension)
    os.close(handle)
    os.remove(filename)

    yield filename

    if os.path.exists(filename):
        if os.path.isdir(filename):
            shutil.rmtree(filename)
        else:
            try:
                os.remove(filename)
            except OSError:  # sometimes we can't remove a generated temp file
                pass
