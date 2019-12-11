#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/10 15:55
http://www.nowamagic.net/academy/detail/13321023
"""
import cgi
import errno
import logging
import os
import socket
import time
import urlparse

from tor import ioloop, iostream, httputil

try:
    import fcntl
except ImportError:
    if os.name == 'nt':
        import win32_support as fcntl
    else:
        raise

try:
    import ssl # Python 2.6+
except ImportError:
    ssl = None


class HTTPRequest(object):

    def __init__(self, method, uri, version="HTTP/1.0", headers=None,
                 body=None, remote_ip=None, protocol=None, host=None,
                 files=None, connection=None):
        self.method = method
        self.uri = uri
        self.version = version
        self.headers = headers or httputil.HTTPHeaders()
        self.body = body or ""
        if connection and connection.xheaders:
            # Squid uses X-Forwarded-For, others use X-Real-Ip
            self.remote_ip = self.headers.get(
                "X-Real-Ip", self.headers.get("X-Forwarded-For", remote_ip))
            self.protocol = self.headers.get("X-Scheme", protocol) or "http"
        else:
            self.remote_ip = remote_ip
            self.protocol = protocol or "http"
        self.host = host or self.headers.get("Host") or "127.0.0.1"
        self.files = files or {}
        self.connection = connection
        self._start_time = time.time()
        self._finish_time = None

        scheme, netloc, path, query, fragment = urlparse.urlsplit(uri)
        self.path = path
        self.query = query
        arguments = cgi.parse_qs(query)
        self.arguments = {}
        for name, values in arguments.iteritems():
            values = [v for v in values if v]
            if values: self.arguments[name] = values
        print "==== 6 request self.path %s ", self.path


class HTTPConnection(object):

    def __init__(self, stream, address, request_callback, no_keep_alive=False,
                 xheaders=False):
        self.stream = stream
        self.address = address
        self.request_callback = request_callback
        self.no_keep_alive = no_keep_alive
        self.xheaders = xheaders
        self._request = None
        self._request_finished = False
        print "===== 3  HTTPConnection"
        self.stream.read_until("\r\n\r\n", self._on_headers)

    def write(self, chunk):
        assert self._request, "Request closed"
        if not self.stream.closed():
            self.stream.write(chunk, self._on_write_complete)

    def finish(self):
        assert self._request, "Request closed"
        self._request_finished = True
        if not self.stream.writing():
            self._finish_request()

    def _on_write_complete(self):
        if self._request_finished:
            self._finish_request()

    def _finish_request(self):
        print "====   finish request "
        if self.no_keep_alive:
            disconnect = True
        else:
            connection_header = self._request.headers.get("Connection")
            if self._request.supports_http_1_1():
                disconnect = connection_header == "close"
            elif ("Content-Length" in self._request.headers
                    or self._request.method in ("HEAD", "GET")):
                disconnect = connection_header != "Keep-Alive"
            else:
                disconnect = True
        self._request = None
        self._request_finished = False
        if disconnect:
            self.stream.close()
            return
        self.stream.read_until("\r\n\r\n", self._on_headers)

    def _on_headers(self, data):
        eol = data.find("\r\n")
        start_line = data[:eol]
        method, uri, version = start_line.split(" ")
        if not version.startswith("HTTP/"):
            raise Exception("Malformed HTTP version in HTTP Request-Line")
        headers = httputil.HTTPHeaders.parse(data[eol:])
        self._request = HTTPRequest(
            connection=self, method=method, uri=uri, version=version,
            headers=headers, remote_ip=self.address[0])

        content_length = headers.get("Content-Length")
        if content_length:
            content_length = int(content_length)
            if content_length > self.stream.max_buffer_size:
                raise Exception("Content-Length too long")
            if headers.get("Expect") == "100-continue":
                self.stream.write("HTTP/1.1 100 (Continue)\r\n\r\n")
            self.stream.read_bytes(content_length, self._on_request_body)
            return
        self.request_callback(self._request)

    def _on_request_body(self, data):
        self._request.body = data
        content_type = self._request.headers.get("Content-Type", "")
        if self._request.method == "POST":
            if content_type.startswith("application/x-www-form-urlencoded"):
                arguments = cgi.parse_qs(self._request.body)
                for name, values in arguments.iteritems():
                    values = [v for v in values if v]
                    if values:
                        self._request.arguments.setdefault(name, []).extend(
                            values)
            elif content_type.startswith("multipart/form-data"):
                if 'boundary=' in content_type:
                    boundary = content_type.split('boundary=', 1)[1]
                    if boundary: self._parse_mime_body(boundary, data)
                else:
                    logging.warning("Invalid multipart/form-data")
        self.request_callback(self._request)

    def _parse_mime_body(self, boundary, data):
        # The standard allows for the boundary to be quoted in the header,
        # although it's rare (it happens at least for google app engine
        # xmpp).  I think we're also supposed to handle backslash-escapes
        # here but I'll save that until we see a client that uses them
        # in the wild.
        if boundary.startswith('"') and boundary.endswith('"'):
            boundary = boundary[1:-1]
        if data.endswith("\r\n"):
            footer_length = len(boundary) + 6
        else:
            footer_length = len(boundary) + 4
        parts = data[:-footer_length].split("--" + boundary + "\r\n")
        for part in parts:
            if not part: continue
            eoh = part.find("\r\n\r\n")
            if eoh == -1:
                logging.warning("multipart/form-data missing headers")
                continue
            headers = httputil.HTTPHeaders.parse(part[:eoh])
            name_header = headers.get("Content-Disposition", "")
            if not name_header.startswith("form-data;") or \
               not part.endswith("\r\n"):
                logging.warning("Invalid multipart/form-data")
                continue
            value = part[eoh + 4:-2]
            name_values = {}
            for name_part in name_header[10:].split(";"):
                name, name_value = name_part.strip().split("=", 1)
                name_values[name] = name_value.strip('"').decode("utf-8")
            if not name_values.get("name"):
                logging.warning("multipart/form-data value missing name")
                continue
            name = name_values["name"]
            if name_values.get("filename"):
                ctype = headers.get("Content-Type", "application/unknown")
                self._request.files.setdefault(name, []).append(dict(
                    filename=name_values["filename"], body=value,
                    content_type=ctype))
            else:
                self._request.arguments.setdefault(name, []).append(value)


class HTTPServer(object):

    def __init__(self, request_callback, no_keep_alive=False, io_loop=None,
                 xheaders=False, ssl_options=None):
        self.request_callback = request_callback
        self.no_keep_alive = no_keep_alive
        self.io_loop = io_loop
        self.xheaders = xheaders
        self.ssl_options = ssl_options
        self._socket = None
        self._started = False
        
    def listen(self, port, address=""):
        self.bind(port, address)
        self.start(1)

    def bind(self, port, address=""):
        
        assert not self._socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        flags = fcntl.fcntl(self._socket.fileno(), fcntl.F_GETFD)
        flags |= fcntl.FD_CLOEXEC
        fcntl.fcntl(self._socket.fileno(), fcntl.F_SETFD, flags)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setblocking(0)
        self._socket.bind((address, port))
        self._socket.listen(128)

    def start(self, num_processes=1):
        
        assert not self._started
        self._started = True
        if num_processes is None or num_processes <= 0:
            # Use sysconf to detect the number of CPUs (cores)
            try:
                num_processes = os.sysconf("SC_NPROCESSORS_CONF")
            except ValueError:
                logging.error("Could not get num processors from sysconf; "
                              "running with one process")
                num_processes = 1
        if num_processes > 1 and ioloop.IOLoop.initialized():
            logging.error("Cannot run in multiple processes: IOLoop instance "
                          "has already been initialized. You cannot call "
                          "IOLoop.instance() before calling start()")
            num_processes = 1
        if num_processes > 1:
            logging.info("Pre-forking %d server processes", num_processes)
            for i in range(num_processes):
                if os.fork() == 0:
                    self.io_loop = ioloop.IOLoop.instance()
                    self.io_loop.add_handler(
                        self._socket.fileno(), self._handle_events,
                        ioloop.IOLoop.READ)
                    return
            os.waitpid(-1, 0)
        else:
            if not self.io_loop:
                self.io_loop = ioloop.IOLoop.instance()
            self.io_loop.add_handler(self._socket.fileno(),
                                     self._handle_events,
                                     ioloop.IOLoop.READ)

    def stop(self):
      self.io_loop.remove_handler(self._socket.fileno())
      self._socket.close()

    def _handle_events(self, fd, events):
        print  "==== 1  _handle_events fd %s, events %s " % (fd, events)
        while True:
            try:
                connection, address = self._socket.accept()
                print "------ connection %s  address %s" % (connection, address)
            except socket.error, e:
                print "return --- e: ", e
                if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    print "errno.EWOULDBLOCK== 10035, errno.EAGAIN == 11 "
                    return
                raise
            if self.ssl_options is not None:
                assert ssl, "Python 2.6+ and OpenSSL required for SSL"
                connection = ssl.wrap_socket(
                    connection, server_side=True, **self.ssl_options)
            try:
                stream = iostream.IOStream(connection, io_loop=self.io_loop)
                HTTPConnection(stream, address, self.request_callback,
                               self.no_keep_alive, self.xheaders)
            except:
                logging.error("Error in connection callback", exc_info=True)