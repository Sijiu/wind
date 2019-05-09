#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/5/1 17:26
"""
import errno
import fcntl
import logging
import os
import select
import time


try:
    import signal
except ImportError:
    signal = None


class IOLoop(object):

    _EPOLLIN = 0x001
    _EPOLLPRI = 0x002
    _EPOLLOUT = 0x004
    _EPOLLERR = 0x008
    _EPOLLHUP = 0x010
    _EPOLLRDHUP = 0x2000
    _EPOLLONESHOT = (1 << 30)
    _EPOLLET = (1 << 31)

    NONE = 0
    READ = _EPOLLIN
    WRITE = _EPOLLOUT
    ERROR = _EPOLLERR | _EPOLLHUP | _EPOLLRDHUP

    def __init__(self, impl=None):
        self._impl = impl or _poll()
        self._handlers = {}
        self._callbacks = set()
        self._events = {}
        self._timeouts = []
        self._running = False
        self._stopped = False
        self._blocking_log_threshold = None

        # create a pipe that we send bogus data to when we want to wake
        # the I?O loop when it is idle
        if os.name != 'nt':
            r, w = os.pipe()
            self._set_nonblocking(r)
            self._set_nonblocking(w)
            self._set_close_exec(r)
            self._set_close_exec(w)
            self._waker_reader = os.fdopen(r, "r", 0)
            self._waker_writer = os.fdopen(w, "w", 0)
            print "===", os.name
        self.add_handler(r, self._read_waker, self.READ)

    @classmethod
    def instance(cls):
        """Returns a global IOLoop instance.

        Most single-threaded applications have a single, global IOLoop.
        Use this method instead of passing around IOLoop instances
        throughout your code.

        A common pattern for classes that depend on IOLoops is to use
        a default argument to enable programs with multiple IOLoops
        but not require the argument for simpler applications:

            class MyClass(object):
                def __init__(self, io_loop=None):
                    self.io_loop = io_loop or IOLoop.instance()
        """
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    @classmethod
    def initialized(cls):
        return hasattr(cls, "_instance")

    def add_handler(self, fd, handler, events):
        self._handlers[fd] = handler
        self._impl.register(fd, events | self.ERROR)

    def start(self):
        """Starts the I/O loop
        The loop will run until one of the I/O handlers call stop(), which will make
        the loop stop after the current event iteration completes
        """
        if self._stopped:
            self._stopped = False
            return
        self._running = True
        while True:
            poll_timeout = 0.2

            callbacks = list(self._callbacks)

            for callback in callbacks:
                print "callback==", callbacks
                if callback in self._callbacks:
                    self._callbacks.remove(callback)
                    self._run_callback(callback)

            if self._callbacks:
                poll_timeout = 0.0

                if self._timeouts:
                    now = time.time()
                    while self._timeouts and self._timeouts[0].deadline <= now:
                        timeout = self._timeouts.pop(0)
                        self._run_callback(timeout.callback)
                    if self._timeouts:
                        milliseconds = self._timeouts[0].deadline - now
                        poll_timeout = min(milliseconds, poll_timeout)

            if not self._running:
                break

            if self._blocking_log_threshold is not None:
                signal.setitimer(signal.ITIMER_REAL, 0, 0)

            try:
                event_pairs = self._impl.poll(poll_timeout)
            except Exception, e:
                if (getattr(e, 'errno') == errno.EINTR or
                    (isinstance(getattr(e, 'args'), tuple) and len(e.args)== 2 and e.args[0] == errno.EINTR)):
                    logging.error("Interrupted system call ", exc_info=1)
                    continue
                else:
                    raise
            if self._blocking_log_threshold is not None:
                signal.setitimer(signal.ITIMER_REAL, self._blocking_log_threshold, 0)

            self._events.update(event_pairs)
            while self._events:
                fd, events = self._events.popitem()
                try:
                    self._handlers[fd](fd, events)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except (OSError, IOError):
                    if e[0] == errno.EPIPE:
                        pass
                    else:
                        logging.error("Exception in I/O handler for fd %d", fd, exc_info=True)

        self._stopped = False
        if self._blocking_log_threshold is not None:
            signal.setitimer(signal.ITIMER_REAL, 0, 0)

    def _run_callback(self, callback):
        try:
            callback()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handle_callback_exception(callback)

    def remove_handler(self, fd):
        """Stop listening for events on fd.
        """
        self._handlers.pop(fd, None)
        self._events.pop(fd, None)
        try:
            self._impl.unregister(fd)
        except (OSError, IOError):
            logging.debug("Error deleting fd from IOLoop", exc_info=True)

    def handle_callback_exception(self, callback):
        """This method is called whenever  callback by the IOLoop throws an exception.
        """
        logging.error("Exception in callback %r ", callback, exc_infp=True)

    def _read_waker(self, fd, events):
        try:
            while True:
                self._waker_reader.read()
        except IOError:
            pass

    def _set_nonblocking(self, fd):
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        fcntl.fcntl(fd, fcntl.F_SETFD, flags | os.O_NONBLOCK)

    def _set_close_exec(self, fd):
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        fcntl.fcntl(fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)



class _KQueue(object):
    """A kqueue-based event loop for BSD/Mac systems."""
    def __init__(self):
        self._kqueue = select.kqueue()
        self._active = {}

    def fileno(self):
        return self._kqueue.fileno()

    def register(self, fd, events):
        self._control(fd, events, select.KQ_EV_ADD)
        self._active[fd] = events

    def modify(self, fd, events):
        self.unregister(fd)
        self.register(fd, events)

    def unregister(self, fd):
        events = self._active.pop(fd)
        self._control(fd, events, select.KQ_EV_DELETE)

    def _control(self, fd, events, flags):
        kevents = []
        if events & IOLoop.WRITE:
            kevents.append(select.kevent(
                    fd, filter=select.KQ_FILTER_WRITE, flags=flags))
        if events & IOLoop.READ or not kevents:
            # Always read when there is not a write
            kevents.append(select.kevent(
                    fd, filter=select.KQ_FILTER_READ, flags=flags))
        # Even though control() takes a list, it seems to return EINVAL
        # on Mac OS X (10.6) when there is more than one event in the list.
        for kevent in kevents:
            self._kqueue.control([kevent], 0)

    def poll(self, timeout):
        kevents = self._kqueue.control(None, 1000, timeout)
        events = {}
        for kevent in kevents:
            fd = kevent.ident
            flags = 0
            if kevent.filter == select.KQ_FILTER_READ:
                events[fd] = events.get(fd, 0) | IOLoop.READ
            if kevent.filter == select.KQ_FILTER_WRITE:
                events[fd] = events.get(fd, 0) | IOLoop.WRITE
            if kevent.flags & select.KQ_EV_ERROR:
                events[fd] = events.get(fd, 0) | IOLoop.ERROR
        return events.items()


if hasattr(select, "epoll"):
    # Python 2.6+ on Linux
    _poll = select.epoll
elif hasattr(select, "kqueue"):
    # Python 2.6+ on BSD or Mac
    _poll = _KQueue
else:
    try:
        # Linux systems with our C module installed
        import epoll
        # _poll = _EPoll
        _poll = select.epoll
    except:
        # All other systems
        import sys
        if "linux" in sys.platform:
            logging.warning("epoll module not found; using select()")
        # _poll = _Select
        _poll = select.epoll