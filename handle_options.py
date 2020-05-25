import handle_users
from create_headers import *
from handle_error import *
import socket

OK = 000
CRLF = '\r\n'

def handle_options(user, request_parsed_data, metadata, connection_socket, stamp) :
    global OK, CRLF
    response_headers = ''
    payload = ''
    message = ''
    content_encoding, transfer_encoding = '', ''

    close_connection = check_connection(request_parsed_data)
    if not close_connection :
        user.accept_next()

    try :
        path, status = get_path(request_parsed_data, metadata)
        if status == OK :
            if not os.access(path, os.R_OK) :
                status = 405
        if status == OK :
            status = check_conditions(request_parsed_data, path)
        if status == OK:
            date_header = create_date_header()
            response_headers += date_header

            allow_header, status = create_allow_header(path)
            response_headers += allow_header

            if status == OK :
                content_lenth_header, status = create_content_lenth_header()
                response_headers += content_lenth_header

                if status == OK:
                    status_line = create_status_line(metadata, status)
                    message = status_line + response_headers + CRLF
                    while user.Stamp != stamp :
                        pass
                    connection_socket.send(message.encode())
                    connection_socket.send(''.encode())
                    user.Stamp += 1

        if status != OK:
            close_connection = handle_error(user, status, connection_socket, metadata, stamp, request_parsed_data)
    except socket.error as msg :
        close_connection = True
    if close_connection :
        user.close_connection(connection_socket)
