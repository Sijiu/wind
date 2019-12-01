#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/30 17:24
"""
import datetime
import socket
import StringIO
import sys
from middleware import TestMiddle


class WSGIServer(object):

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 1

    def __init__(self, server_address):
        # Create a listening socket
        self.listen_socket = listen_socket = socket.socket(self.address_family, self.socket_type)
        # 可以重复使用同一个地址
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定端口
        listen_socket.bind(server_address)
        # 激活启用
        listen_socket.listen(self.request_queue_size)
        # 获取服务主机和端口
        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        # 返回有Web框架或者应用设置的头部
        self.headers_set = []

    def set_app(self, application):
        print "============= %s" % application
        print application
        self.application = application

    def server_forever(self):
        listen_socket = self.listen_socket
        while True:
            # 新的客户端连接
            self.client_connection, client_address = listen_socket.accept()
            # 处理一个请求并且关闭客户端连接, 然后循环等待另一个客户端连接
            self.handle_one_request()

    def handle_one_request(self):
        self.request_data = request_data = self.client_connection.recv(1024)
        # Print formatted request data a la "curl -v"
        print "".join('< %s \n' % line for line in request_data.splitlines())
        try:
            self.parse_request(request_data)

            # Construct environment dictionary using request data
            # 使用请求数据构造 环境字典
            env = self.get_environ()

            # It's time to call our callable and get back a result that will become HTTP request body
            # print env, self.start_response()
            result = self.application(env, self.start_response)

            # Construct a response and send it back to the client
            self.finish_response(result)
        except Exception as e:
            print "@@@@@@@  %s" % e

    def parse_request(self, text=" GET /index HTTP/1.1"):
        request_line = text.splitlines()[0]
        request_line = request_line.rstrip("\r\n")
        self.request_dict = {}
        for itm in text.splitlines()[1:]:
            if ':' in itm:
                self.request_dict[itm.split(':')[0]] = itm.split(':')[1]
        # Break down the request line into components 将请求分解
        (self.request_method, self.path, self.request_version) = request_line.split()

    def get_environ(self):
        env = {}
        # 必须的 WSGI变量
        env["wsgi.version"] = (1, 0)
        env["wsgi.url_scheme"] = 'http'
        env["wsgi.input"] = StringIO.StringIO(self.request_data)
        env["wsgi.errors"] = sys.stderr
        env["wsgi.multithread"] = False
        env["wsgi.multiprocess"] = False
        env["wsgi.run_once"] = False

        # CGI 必须的变量
        env["REQUEST_METHOD"] = self.request_method  # GET
        env["PATH_INFO"] = self.path  # /index
        env["SERVER_NAME"] = self.server_name  # localhost
        env["SERVER_PORT"] = str(self.server_port)  # 8889
        env["USER_AGENT"] = self.request_dict.get('User-Agent')
        return env

    def start_response(self, status, response_headers, exc_info=None):
        # Add Necessary server headers 添加需要的请求头
        # server_headers = [('Date',  '2019年11月30日18:01:53'),
        # 'ascii' codec can't decode byte 0xe5 in position 10: ordinal not in range(128)
        print "response_headers===", response_headers
        server_headers = [('Date',  datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')),
                          ('Server', 'Base WSGIServer 0.2')]
        self.headers_set = [status, response_headers + server_headers]
        # To adhere to WSGI specification the start_response must return a 'write' callable. We simplicity sake we'll
        # ignore that detail for now
        # return finish_response

    def finish_response(self, result):
        try:
            status, response_headers = self.headers_set
            response = 'HTTP/1.1 %s\r\n' % status
            for header in response_headers:
                response += '%s: %s\r\n' % (header[0], header[1])
            response += "\r\n"
            for data in result:
                response += data

            print "".join("> %s \n" % line for line in response.splitlines())
            self.client_connection.sendall(response)
        finally:
            self.client_connection.close()


SERVER_ADDRESS = (HOST, PORT) = "", 8888


def make_server(server_address, application):
    server = WSGIServer(server_address)
    server.set_app(TestMiddle(application))
    return server


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("请提供一个形如 module:callable 的应用对象")
    app_path = sys.argv[1]
    module, application = app_path.split(":")
    module = __import__(module)
    application = getattr(module, application)
    httpd = make_server(SERVER_ADDRESS, application)
    print "WSGIServer: serving HTTP on port %s ...\n" % PORT
    httpd.server_forever()