#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/5/1 12:43
"""
import httplib
import logging
import re


class HTTPError(Exception):

    def __init__(self, status_code, log_message=None, *args):
        self.status_code = status_code
        self.log_message = log_message
        self.args = args

    def __str__(self):
        message = "HTTP %d: %s" % (self.status_code, httplib.responses[self.status_code])
        if self.log_message:
            return message + " (" + (self.log_message % self.args) + ") "
        return message


class RequestHandler(object):
    """Subclass this class and define get() or post() to make a handler
    """
    SUPPORTED_METHODS = ("GET", "POST", "HEAD", "PUT")

    def __init__(self, application, request):
        self.request = request
        self._finished = False
        self._auto_finish = True
        # self._transforms = transforms or []
        self._header_written = False
        self.clear()
        # Check since connection is not available in WSGI
        if hasattr(self.request, "connection"):
            self.request.connection.stream.set_close_callback(self.on_connection_close)

    def get(self, *args, **kwargs):
        raise HTTPError(405)

    def on_connection_close(self):
        pass

    def clear(self):
        """Reset all headers and content for this response. """
        self._headers = {
            "Server": "MornadoServer/1.0",
            "Content-Type": "text/html; charset=UTF-8",
        }
        if not self.request.supports_http_1_1():
            pass
        self._write_buffer = []
        self._status_code = 200

    def write(self, chunk):
        assert not self._finished
        if isinstance(chunk, dict):
            pass
            # chunk = escape.json_encode()
        chunk = _utf8(chunk)
        self._write_buffer.append(chunk)


class Application(object):

    def __init__(self, handlers=None, default_host="", **settings):
        self.handlers = []
        self.named_handlers = {}
        self.default_host = default_host
        self.settings = settings

        if self.settings.get("static_path"):
            path = self.settings["static_path"]
        if handlers: self.add_handlers(".*$", handlers)

        # automatically reload modified modules
        if self.settings.get("debug"):
            import autoreload
            autoreload.start()

    def add_handlers(self, host_pattern, host_handlers):
        """ Appends the given handlers to our handler list."""
        if not host_pattern.endswith("$"):
            host_pattern += "$"
        handlers = []
        if self.handlers and self.handlers[-1][0].pattern == ".*$":
            print type(self.handlers)
            print self.handlers
            self.handlers.insert(-1, (re.compile(host_pattern), handlers))
        else:
            self.handlers.append((re.compile(host_pattern), handlers))

        for spec in host_handlers:
            if type(spec) is type(()):
                assert len(spec) in (2, 3)
                pattern, handler = spec[0], spec[1]
                if len(spec) == 3:
                    kwargs = spec[2]
                else:
                    kwargs = {}
                kwargs = spec[2] if len(spec) == 3 else {}
                spec = URLSpec(pattern, handler, kwargs)
            handlers.append(spec)
            if spec.name:
                if spec.name in self.named_handlers:
                    logging.warning("Multiple handlers named %s replacing ", spec.name)
                self.named_handlers[spec.name] = spec


class URLSpec(object):
    """Specifies mappings between URLs and handlers."""
    def __init__(self, pattern, handler_class, kwargs={}, name=None):
        """Creates a URLSpec.

        Parameters:
        pattern: Regular expression to be matched.  Any groups in the regex
            will be passed in to the handler's get/post/etc methods as
            arguments.
        handler_class: RequestHandler subclass to be invoked.
        kwargs (optional): A dictionary of additional arguments to be passed
            to the handler's constructor.
        name (optional): A name for this handler.  Used by
            Application.reverse_url.
        """
        if not pattern.endswith('$'):
            pattern += '$'
        self.regex = re.compile(pattern)
        self.handler_class = handler_class
        self.kwargs = kwargs
        self.name = name
        self._path, self._group_count = self._find_groups()

    def _find_groups(self):
        """Returns a tuple (reverse string, group count) for a url.

        For example: Given the url pattern /([0-9]{4})/([a-z-]+)/, this method
        would return ('/%s/%s/', 2).
        """
        pattern = self.regex.pattern
        if pattern.startswith('^'):
            pattern = pattern[1:]
        if pattern.endswith('$'):
            pattern = pattern[:-1]

        if self.regex.groups != pattern.count('('):
            # The pattern is too complicated for our simplistic matching,
            # so we can't support reversing it.
            return (None, None)

        pieces = []
        for fragment in pattern.split('('):
            if ')' in fragment:
                paren_loc = fragment.index(')')
                if paren_loc >= 0:
                    pieces.append('%s' + fragment[paren_loc + 1:])
            else:
                pieces.append(fragment)

        return (''.join(pieces), self.regex.groups)

    def reverse(self, *args):
        assert self._path is not None, \
            "Cannot reverse url regex " + self.regex.pattern
        assert len(args) == self._group_count, "required number of arguments "\
            "not found"
        if not len(args):
            return self._path
        return self._path % tuple([str(a) for a in args])


url = URLSpec


def _utf8(s):
    if isinstance(s, unicode):
        return s.encode("utf-8")
    assert isinstance(s, str)
    return s


class StaticFileHandler(RequestHandler):
    # def __init__(self, application, request, path):
    def __init__(self, request):
        RequestHandler.__init__(request)


class _O(dict):
    def __getattr__(self, name):
        try:
            return self(name)
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value
