import threading
import os
import socket
import logging
from handle_request import *
import handle_get, handle_head, handle_post, handle_put, handle_delete, handle_options
import handle_error, create_headers

class Handle_User :
    def __init__(self, server):
        self.CLOSE_CONNECTION = False
        self.ACCEPT_NEXT = True
        self.CRLF = '\r\n'
        self.OK = 000
        self.Stamp = 0
        self.server = server
        self.request_threads = []

    def handle_user(self, server, connection_socket, addr) :
        stamp = 0
        create_headers.DEFAULT_PATH = server.get_metadata()['DocumentRoot']
        while (not self.CLOSE_CONNECTION) :
            while (not self.ACCEPT_NEXT) and (not self.CLOSE_CONNECTION):
                pass
            if self.CLOSE_CONNECTION :
                break
            self.ACCEPT_NEXT = False
            request, error = self.get_request(connection_socket)
            if not error :
                if request:
                    t = threading.Thread(target = self.handle_request, args = (request, server, connection_socket, stamp)).start()
                    self.request_threads.append(t)
                    stamp += 1
            else :
                break
        print('closed !!')

    def get_request(self, connection_socket):
        CR, LF = '\r'.encode(), '\n'.encode()
        request = ''
        pattern = [CR, LF, CR, LF]
        index = 0
        error = False

        try :
            char1 = connection_socket.recv(1)
            char2 = connection_socket.recv(1)
            while char1 == CR and char2 == LF:
                char1 = connection_socket.recv(1)
                char2 = connection_socket.recv(1)
            if char1 != CR:
                request = char1 + char2
            char = char2
            if char == pattern[index]:
                index += 1
            while index != 4 and (not self.CLOSE_CONNECTION) :
                char = connection_socket.recv(1)
                if char == pattern[index]:
                    index += 1
                else:
                    index = 0
                request += char
        except socket.error as msg :
            error = True
        if (not request) or self.CLOSE_CONNECTION :
            error = True
        request = request.decode()
        return request, error

    def method_handler(self, method) :
        functions = {
            'GET' : handle_get.handle_get,
            'HEAD' : handle_head.handle_head,
            'POST' : handle_post.handle_post,
            'PUT' : handle_put.handle_put,
            'DELETE' : handle_delete.handle_delete,
            'OPTIONS': handle_options.handle_options
        }
        return functions[method]
    
    
    def handle_request(self, request, server, connection_socket, stamp):
        request_parsed_data = {}
        request_parsed_data['method'] = None
        request_parsed_data['target_resource'] = None
        request_parsed_data['http_version'] = None
        request_parsed_data['headers'] = None
        metadata = server.get_metadata()

        logging.basicConfig(filename = metadata['LOG_FILENAME'],
                            format = '%(asctime)s %(message)s',
                            filemode = 'a')
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        metadata = server.get_metadata()
        request_line, headers, payload, status = self.get_components(request)
        if status == self.OK :
            method, target_resource, http_version, status = parse_requestline(request_line, metadata)
            if status == self.OK :
                request_parsed_data['method'] = method
                request_parsed_data['target_resource'] = target_resource
                request_parsed_data['http_version'] = http_version
                logger.info(' : ' + method + ' ,' + target_resource + ' ,' + http_version)
                parsed_header, status = parse_headers(headers, metadata)
                request_parsed_data['headers'] = parsed_header
                self.method_handler(method)(self, request_parsed_data, metadata, connection_socket, stamp)
            else:
                handle_error.handle_error(self, status, connection_socket, metadata, stamp)
        else:
            handle_error.handle_error(self, status, connection_socket, metadata, stamp)
    
    # GETTING COMPONENTS - REQUEST_LINE, HEADERS AND PAYLOAD
    def get_components(self, request):
        request_line = ''
        headers = ''
        payload = ''
        status = self.OK
        received_requestline = False
        received_first_header = False
        received_headers = False
        segments = request.split(self.CRLF)
    
        for segment in segments:
            if not received_requestline:
                if segment == '':
                    pass
                else:
                    request_line = segment
                    received_requestline = True
            elif not received_first_header:
                if segment != '':
                    headers += segment + self.CRLF
                    received_first_header = True
                else:
                    status = 400 #bad request
                    return request_line, headers, payload, status
            elif not received_headers:
                if segment != '':
                    headers += segment + self.CRLF
                else:
                    request_headers = True
            else:
                payload += segment
        return request_line, headers, payload, status

    def accept_next(self) :
        self.ACCEPT_NEXT = True

    def close_connection(self, connection_socket) :
        print('closing connection -->', end = ' ')
        self.server.remove_user(self)
        try :
            connection_socket.shutdown(socket.SHUT_RDWR)
        except :
            pass
        self.CLOSE_CONNECTION = True
