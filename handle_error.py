from create_headers import *
import handle_users
import socket

status_to_path = {
    400 : '400.html',
    401 : '401.html',
    405 : '405.html',
    500 : '500.html'
}
def handle_error(user, status, connection_socket, metadata, stamp, request_parsed_data = '') :
    if not request_parsed_data :
        user.accept_next()
    response_headers = ''
    payload = ''
    transfer_encoding = 'chunked'
    close_connection = False

    method = ''
    if request_parsed_data :
        method = request_parsed_data['method']

    path = status_to_path[status]

    status_line = create_status_line(metadata, status)
    content_type_header = 'Content-Type: text/html' + CRLF
    content_lenth_header = 'Content-Length:' + str(os.path.getsize(path)) + CRLF
    if status == 401 :
        response_headers += create_www_authenticate_header()
    response_headers = content_type_header + content_lenth_header
    message = status_line + response_headers + CRLF
    file = open(path, 'rb')
    payload = file.read(os.path.getsize(path))
    while user.Stamp != stamp:
        pass
    try :
        connection_socket.send(message.encode())
        if method != 'HEAD' :
            connection_socket.send(payload)
        user.Stamp += 1
    except socket.error as msg :
        close_connection = True
    return close_connection
