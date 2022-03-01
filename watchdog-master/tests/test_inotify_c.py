
import pytest
from watchdog.utils import platform

if not platform.is_linux():  # noqa
    pytest.skip("GNU/Linux only.", allow_module_level=True)

import contextlib
import ctypes
import errno
import logging
import os
import struct
from functools import partial
from queue import Queue

from watchdog.events import DirCreatedEvent, DirDeletedEvent, DirModifiedEvent
from watchdog.observers.api import ObservedWatch
from watchdog.observers.inotify import InotifyFullEmitter, InotifyEmitter
from watchdog.observers.inotify_c import Inotify, InotifyConstants, InotifyEvent

from .shell import mkdtemp, rm


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def setup_function(function):
    global p, event_queue
    tmpdir = os.path.realpath(mkdtemp())
    p = partial(os.path.join, tmpdir)
    event_queue = Queue()


@contextlib.contextmanager
def watching(path=None, use_full_emitter=False):
    path = p('') if path is None else path
    global emitter
    Emitter = InotifyFullEmitter if use_full_emitter else InotifyEmitter
    emitter = Emitter(event_queue, ObservedWatch(path, recursive=True))
    emitter.start()
    yield
    emitter.stop()
    emitter.join(5)


def teardown_function(function):
    rm(p(''), recursive=True)
    try:
        assert not emitter.is_alive()
    except NameError:
        pass


def struct_inotify(wd, mask, cookie=0, length=0, name=b""):
    assert len(name) <= length
    struct_format = (
        "="  # (native endianness, standard sizes)
        "i"  # int      wd
        "i"  # uint32_t mask
        "i"  # uint32_t cookie
        "i"  # uint32_t len
        "%ds" % (length,)  # char[] name
    )
    return struct.pack(struct_format, wd, mask, cookie, length, name)


def test_late_double_deletion(monkeypatch):
    inotify_fd = type(str("FD"), (object,), {})()  # Empty object
    inotify_fd.last = 0
    inotify_fd.wds = []

    const = InotifyConstants()

    # CREATE DELETE CREATE DELETE DELETE_SELF IGNORE DELETE_SELF IGNORE
    inotify_fd.buf = (
        struct_inotify(wd=1, mask=const.IN_CREATE | const.IN_ISDIR,
                       length=16, name=b"subdir1")
        + struct_inotify(wd=1, mask=const.IN_DELETE | const.IN_ISDIR,
                         length=16, name=b"subdir1")
    ) * 2 + (
        struct_inotify(wd=2, mask=const.IN_DELETE_SELF)
        + struct_inotify(wd=2, mask=const.IN_IGNORED)
        + struct_inotify(wd=3, mask=const.IN_DELETE_SELF)
        + struct_inotify(wd=3, mask=const.IN_IGNORED)
    )

    os_read_bkp = os.read

    def fakeread(fd, length):
        if fd is inotify_fd:
            result, fd.buf = fd.buf[:length], fd.buf[length:]
            return result
        return os_read_bkp(fd, length)

    os_close_bkp = os.close

    def fakeclose(fd):
        if fd is not inotify_fd:
            os_close_bkp(fd)

    def inotify_init():
        return inotify_fd

    def inotify_add_watch(fd, path, mask):
        fd.last += 1
        logger.debug("New wd = %d" % fd.last)
        fd.wds.append(fd.last)
        return fd.last

    def inotify_rm_watch(fd, wd):
        logger.debug("Removing wd = %d" % wd)
        fd.wds.remove(wd)
        return 0

    # Mocks the API!
    from watchdog.observers import inotify_c
    monkeypatch.setattr(os, "read", fakeread)
    monkeypatch.setattr(os, "close", fakeclose)
    monkeypatch.setattr(inotify_c, "inotify_init", inotify_init)
    monkeypatch.setattr(inotify_c, "inotify_add_watch", inotify_add_watch)
    monkeypatch.setattr(inotify_c, "inotify_rm_watch", inotify_rm_watch)

    with watching(p('')):
        # Watchdog Events
        for evt_cls in [DirCreatedEvent, DirDeletedEvent] * 2:
            event = event_queue.get(timeout=5)[0]
            assert isinstance(event, evt_cls)
            assert event.src_path == p('subdir1')
            event = event_queue.get(timeout=5)[0]
            assert isinstance(event, DirModifiedEvent)
            assert event.src_path == p('').rstrip(os.path.sep)

    assert inotify_fd.last == 3  # Number of directories
    assert inotify_fd.buf == b""  # Didn't miss any event
    assert inotify_fd.wds == [2, 3]  # Only 1 is removed explicitly


def test_raise_error(monkeypatch):
    func = Inotify._raise_error

    monkeypatch.setattr(ctypes, "get_errno", lambda: errno.ENOSPC)
    with pytest.raises(OSError) as exc:
        func()
    assert exc.value.errno == errno.ENOSPC
    assert "inotify watch limit reached" in str(exc.value)

    monkeypatch.setattr(ctypes, "get_errno", lambda: errno.EMFILE)
    with pytest.raises(OSError) as exc:
        func()
    assert exc.value.errno == errno.EMFILE
    assert "inotify instance limit reached" in str(exc.value)

    monkeypatch.setattr(ctypes, "get_errno", lambda: errno.ENOENT)
    with pytest.raises(OSError) as exc:
        func()
    assert exc.value.errno == errno.ENOENT
    assert "No such file or directory" in str(exc.value)

    monkeypatch.setattr(ctypes, "get_errno", lambda: -1)
    with pytest.raises(OSError) as exc:
        func()
    assert exc.value.errno == -1
    assert "Unknown error -1" in str(exc.value)


def test_non_ascii_path():
    """
    Inotify can construct an event for a path containing non-ASCII.
    """
    path = p(u"\N{SNOWMAN}")
    with watching(p('')):
        os.mkdir(path)
        event, _ = event_queue.get(timeout=5)
        assert isinstance(event.src_path, type(u""))
        assert event.src_path == path
        # Just make sure it doesn't raise an exception.
        assert repr(event)


def test_watch_file():
    path = p("this_is_a_file")
    with open(path, "a"):
        pass
    with watching(path):
        os.remove(path)
        event, _ = event_queue.get(timeout=5)
        assert repr(event)


def test_event_equality():
    wd_parent_dir = 42
    filename = "file.ext"
    full_path = p(filename)
    event1 = InotifyEvent(
        wd_parent_dir, InotifyConstants.IN_CREATE, 0, filename, full_path)
    event2 = InotifyEvent(
        wd_parent_dir, InotifyConstants.IN_CREATE, 0, filename, full_path)
    event3 = InotifyEvent(
        wd_parent_dir, InotifyConstants.IN_ACCESS, 0, filename, full_path)
    assert event1 == event2
    assert event1 != event3
    assert event2 != event3
