#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/5/1 17:26
"""
import errno
import logging
import os
import select
import time


try:
    import signal
except ImportError:
    signal = None

try:
    import fcntl
except ImportError:
    if os.name == 'nt':
        import win32_support
        import win32_support as fcntl
    else:
        raise


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
        # 目前只是一个 list pop
        # 新版本将是一个最小堆结构，按照超时时间从小到大排列的 fd 的任务堆（ 通常这个任务都会包含一个 callback ）
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
        else:
            self._waker_reader = self._waker_writer = win32_support.Pipe()
            r = self._waker_writer.reader_fd
            print "passsssssss  ", os.name
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

    # epoll_ctl：这个三个方法分别对应 epoll_ctl 中的
    #  add 、 modify 、 del 参数。 所以这三个方法实现了 epoll 的 epoll_ctl 。
    def add_handler(self, fd, handler, events):
        self._handlers[fd] = handler
        self._impl.register(fd, events | self.ERROR)

    def update_handler(self, fd, events):
        """ Changes the events we listen for fd
        """
        self._impl.modify(fd, events| self.ERROR)

    def remove_handler(self, fd):
        """Stop listening for events on fd.
        """
        self._handlers.pop(fd, None)
        self._events.pop(fd, None)
        try:
            self._impl.unregister(fd)
        except (OSError, IOError):
            logging.debug("Error deleting fd from IOLoop", exc_info=True)

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

            if self._callbacks: # _callbacks 里有数据时
                poll_timeout = 0.0  # 设置 epoll_wait 时间为0（ 立即返回 ）
                # 判断 _timeouts 里是否有数据
            if self._timeouts:
                # 获取当前时间 判断 _timeouts 里的任务有没有超时
                # _timeouts 有数据时一直循环, _timeouts 是个最小堆，第一个数据永远是最小的， 这里第一个数据永远是最接近超时或已超时的
                now = time.time()
                while self._timeouts and self._timeouts[0].deadline <= now:
                    timeout = self._timeouts.pop(0)  # 直接弹出 最后一个
                    self._run_callback(timeout.callback)  # 超时就加到已超时列表里。
                if self._timeouts:
                    # 取最小过期时间当 epoll_wait 等待时间，这样当第一个任务过期时立即返回
                    milliseconds = self._timeouts[0].deadline - now
                    poll_timeout = min(milliseconds, poll_timeout)

            # 检查是否有系统信号中断运行，有则中断，无则继续
            if not self._running:
                break

            # 开始 epoll_wait 之前确保 signal alarm 都被清空（ 这样在 epoll_wait 过程中不会被 signal alarm 打断 ）
            if self._blocking_log_threshold is not None:
                signal.setitimer(signal.ITIMER_REAL, 0, 0)

            try:
                event_pairs = self._impl.poll(poll_timeout) # 获取返回的活跃事件队
            except Exception, e:
                if (getattr(e, 'errno') == errno.EINTR or
                    (isinstance(getattr(e, 'args'), tuple) and len(e.args)== 2 and e.args[0] == errno.EINTR)):
                    logging.error("Interrupted system call ", exc_info=1)
                    continue
                else:
                    raise
            if self._blocking_log_threshold is not None:
                #  epoll_wait 结束， 再设置 signal alarm
                signal.setitimer(signal.ITIMER_REAL, self._blocking_log_threshold, 0)

            self._events.update(event_pairs)

            while self._events:
                fd, events = self._events.popitem()
                print "fd %s==== events %s" % (fd, events)
                try:
                    # 处理事件
                    self._handlers[fd](fd, events)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except (OSError, IOError):
                    if e[0] == errno.EPIPE:
                        pass
                    else:
                        logging.error("Exception in I/O handler for fd %d", fd, exc_info=True)

        self._stopped = False
        # 清空 signal alarm
        if self._blocking_log_threshold is not None:
            signal.setitimer(signal.ITIMER_REAL, 0, 0)

    def stop(self):

        self._running = False
        self._stopped = True
        self._wake()

    def _run_callback(self, callback):
        try:
            callback()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handle_callback_exception(callback)

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

    def _wake(self):
        """
        向 pipe 写入随意字符唤醒 ioloop 事件循环
        """
        try:
            self._waker_writer.write("x")
        except IOError:
            pass


class _EPoll(object):
    """An epoll-based event loop using our C module for Python 2.5 systems"""
    _EPOLL_CTL_ADD = 1
    _EPOLL_CTL_DEL = 2
    _EPOLL_CTL_MOD = 3

    def __init__(self):
        self._epoll_fd = epoll.epoll_create()

    def fileno(self):
        return self._epoll_fd

    def register(self, fd, events):
        epoll.epoll_ctl(self._epoll_fd, self._EPOLL_CTL_ADD, fd, events)

    def modify(self, fd, events):
        epoll.epoll_ctl(self._epoll_fd, self._EPOLL_CTL_MOD, fd, events)

    def unregister(self, fd):
        epoll.epoll_ctl(self._epoll_fd, self._EPOLL_CTL_DEL, fd, 0)

    def poll(self, timeout):
        return epoll.epoll_wait(self._epoll_fd, int(timeout * 1000))


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


class _Select(object):
    """A simple, select()-based IOLoop implementation for non-Linux systems"""
    def __init__(self):
        self.read_fds = set()
        self.write_fds = set()
        self.error_fds = set()
        self.fd_sets = (self.read_fds, self.write_fds, self.error_fds)

    def register(self, fd, events):
        if events & IOLoop.READ: self.read_fds.add(fd)
        if events & IOLoop.WRITE: self.write_fds.add(fd)
        if events & IOLoop.ERROR: self.error_fds.add(fd)

    def modify(self, fd, events):
        self.unregister(fd)
        self.register(fd, events)

    def unregister(self, fd):
        self.read_fds.discard(fd)
        self.write_fds.discard(fd)
        self.error_fds.discard(fd)

    def poll(self, timeout):
        readable, writeable, errors = select.select(
            self.read_fds, self.write_fds, self.error_fds, timeout)
        events = {}
        for fd in readable:
            events[fd] = events.get(fd, 0) | IOLoop.READ
        for fd in writeable:
            events[fd] = events.get(fd, 0) | IOLoop.WRITE
        for fd in errors:
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
        _poll = _EPoll
        # _poll = select.epoll
    except:
        # All other systems
        import sys
        if "linux" in sys.platform:
            logging.warning("epoll module not found; using select()")
        _poll = _Select


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
        _poll = _EPoll
    except:
        # All other systems
        import sys
        if "linux" in sys.platform:
            logging.warning("epoll module not found; using select()")
        _poll = _Select