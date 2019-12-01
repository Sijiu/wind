#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/5/1 12:43
"""
import hashlib
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

    def __init__(self, application, request, transform=None):
        self.application = application
        self.request = request
        self._finished = False
        self._headers_written = False
        self._auto_finish = True
        self._transforms = transform or []
        self._header_written = False
        self.clear()
        # Check since connection is not available in WSGI
        if hasattr(self.request, "connection"):
            self.request.connection.stream.set_close_callback(self.on_connection_close)

    def _execute(self, transforms, *args, **kwargs):
        """Executes this request with the given output transforms."""
        self._transforms = transforms
        try:
            if self.request.method not in self.SUPPORTED_METHODS:
                raise HTTPError(405)
            # If XSRF cookies are turned on, reject form submissions without
            # the proper cookie
            if self.request.method == "POST" and \
               self.application.settings.get("xsrf_cookies"):
                self.check_xsrf_cookie()
            self.prepare()
            if not self._finished:
                getattr(self, self.request.method.lower())(*args, **kwargs)
                if self._auto_finish and not self._finished:
                    self.finish()
        except Exception, e:
            self._handle_request_exception(e)

    def get(self, *args, **kwargs):
        raise HTTPError(405)

    def prepare(self):
        pass

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

    def flush(self, include_footers=False):
        """Flushes the current output buffer to the nextwork."""
        if self.application._wsgi:
            raise Exception("WSGI applications do not support flush()")

        chunk = "".join(self._write_buffer)
        self._write_buffer = []
        if not self._headers_written:
            self._headers_written = True
            for transform in self._transforms:
                self._headers, chunk = transform.transform_first_chunk(
                    self._headers, chunk, include_footers)
            # headers = self._generate_headers()
        else:
            for transform in self._transforms:
                chunk = transform.transform_chunk(chunk, include_footers)
            headers = ""

        # Ignore the chunk and only write the headers for HEAD requests
        if self.request.method == "HEAD":
            if headers: self.request.write(headers)
            return

        # if headers or chunk:
        #     self.request.write(headers + chunk)

    def finish(self, chunk=None):
        """Finishes this response, ending the HTTP request."""
        assert not self._finished
        if chunk is not None: self.write(chunk)

        # Automatically support ETags and add the Content-Length header if
        # we have not flushed any content yet.
        if not self._headers_written:
            if (self._status_code == 200 and self.request.method == "GET"):
                    # and "Etag" not in self._headers):
                hasher = hashlib.sha1()
                for part in self._write_buffer:
                    hasher.update(part)
                etag = '"%s"' % hasher.hexdigest()
                inm = self.request.headers.get("If-None-Match")
                if inm and inm.find(etag) != -1:
                    self._write_buffer = []
                    self.set_status(304)
                else:
                    print 'self.set_header("Etag", etag)'
                    pass
                    # self.set_header("Etag", etag)
            # if "Content-Length" not in self._headers:
            #     content_length = sum(len(part) for part in self._write_buffer)
            #     self.set_header("Content-Length", content_length)

        if hasattr(self.request, "connection"):
            # Now that the request is finished, clear the callback we
            # set on the IOStream (which would otherwise prevent the
            # garbage collection of the RequestHandler when there
            # are keepalive connections)
            self.request.connection.stream.set_close_callback(None)

        # if not self.application._wsgi:
        self.flush(include_footers=True)
        self.request.finish()
        self._log()
        self._finished = True

    def _log(self):
        if self._status_code < 400:
            log_method = logging.info
        elif self._status_code < 500:
            log_method = logging.warning
        else:
            log_method = logging.error
        request_time = 1000.0 * self.request.request_time()
        log_method("%d %s %.2fms", self._status_code,
                   self._request_summary(), request_time)

    def _request_summary(self):
        return self.request.method + " " + self.request.uri + " (" + self.request.remote_ip + ")"

    def _handle_request_exception(self, e):
        if isinstance(e, HTTPError):
            if e.log_message:
                format = "%d %s: " + e.log_message
                args = [e.status_code, self._request_summary()] + list(e.args)
                logging.warning(format, *args)
            if e.status_code not in httplib.responses:
                logging.error("Bad HTTP status code: %d", e.status_code)
                self.send_error(500, exception=e)
            else:
                self.send_error(e.status_code, exception=e)
        else:
            logging.error("Uncaught exception %s\n%r", self._request_summary(),
                          self.request, exc_info=e)
            self.send_error(500, exception=e)

    def set_status(self, status_code):
        """Sets the status code for our response."""
        assert status_code in httplib.responses
        self._status_code = status_code

    def send_error(self, status_code=500, **kwargs):
        """Sends the given HTTP error code to the browser.

        We also send the error HTML for the given error code as returned by
        get_error_html. Override that method if you want custom error pages
        for your application.
        """
        if self._headers_written:
            logging.error("Cannot send error response after headers written")
            if not self._finished:
                self.finish()
            return
        self.clear()
        self.set_status(status_code)
        message = self.get_error_html(status_code, **kwargs)
        self.finish(message)

    def get_error_html(self, status_code, **kwargs):
        """Override to implement custom error pages.

        If this error was caused by an uncaught exception, the
        exception object can be found in kwargs e.g. kwargs['exception']
        """
        return "<html><title>%(code)d: %(message)s</title>" \
               "<body>%(code)d: %(message)s</body></html>" % {
            "code": status_code,
            "message": httplib.responses[status_code],
        }


class Application(object):

    def __init__(self, handlers=None, default_host="", transforms=None, wsgi=False,
                 **settings):
        if transforms is None:
            self.transforms = []
            # if settings.get("gzip"):
            #     self.transforms.append(GZipContentEncoding)
            # self.transforms.append(ChunkedTransferEncoding)
        else:
            self.transforms = transforms
        self.handlers = []
        self._wsgi = wsgi
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

    def __call__(self, request):
        """Called by HTTPServer to execute the request."""
        transforms = [t(request) for t in self.transforms]
        handler = None
        args = []
        kwargs = {}
        handlers = self._get_host_handlers(request)
        if not handlers:
            handler = RedirectHandler(
                request, "http://" + self.default_host + "/")
        else:
            for spec in handlers:
                match = spec.regex.match(request.path)
                if match:
                    # None-safe wrapper around urllib.unquote to handle
                    # unmatched optional groups correctly
                    def unquote(s):
                        if s is None: return s
                        return urllib.unquote(s)
                    handler = spec.handler_class(self, request, **spec.kwargs)
                    # Pass matched groups to the handler.  Since
                    # match.groups() includes both named and unnamed groups,
                    # we want to use either groups or groupdict but not both.
                    kwargs = dict((k, unquote(v))
                                  for (k, v) in match.groupdict().iteritems())
                    if kwargs:
                        args = []
                    else:
                        args = [unquote(s) for s in match.groups()]
                    break
            if not handler:
                handler = ErrorHandler(self, request, 404)

        # In debug mode, re-compile templates and reload static files on every
        # request so you don't need to restart to see changes
        if self.settings.get("debug"):
            if getattr(RequestHandler, "_templates", None):
              map(lambda loader: loader.reset(),
                  RequestHandler._templates.values())
            RequestHandler._static_hashes = {}

        handler._execute(transforms, *args, **kwargs)
        return handler

    def _get_host_handlers(self, request):
        host = request.host.lower().split(':')[0]
        for pattern, handlers in self.handlers:
            if pattern.match(host):
                return handlers
        # Look for default host if not behind load balancer (for debugging)
        if "X-Real-Ip" not in request.headers:
            for pattern, handlers in self.handlers:
                if pattern.match(self.default_host):
                    return handlers
        return None


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
