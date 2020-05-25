import handle_users
from create_headers import *
from handle_error import *
import re

OK = 000
CRLF = '\r\n'

def handle_put(user, request_parsed_data, metadata, connection_socket, stamp):
    global OK, CRLF
    status = OK
    status_line = ''
    headers = request_parsed_data['headers']

    close_connection = check_connection(request_parsed_data)
    #HANDLING INCOMING DATA
    try :
        path, status = get_path(request_parsed_data, metadata)
        if status == OK and os.path.exists(path):
            if not os.access(path, os.W_OK):
                status = 405
        if (status == OK) and ('Content-Type' in headers) :
            content_type = headers['Content-Type']
            media_type = content_type['media-type']
            media_subtype = content_type['media-subtype']
            payload, status = get_payload(request_parsed_data, connection_socket)

            if status == OK :
                status = save_payload(payload, path)
        else :
            status = 400

        #CREATING RESPONSE
        if status == OK :
            response_headers = ''
            payload = ''
            message = ''
            content_encoding, transfer_encoding = '', ''

            date_header = create_date_header()
            response_headers += date_header

            content_type_header, status = create_content_type_header(request_parsed_data, path)
            if status == OK:
                response_headers += content_type_header

            if status == OK:
                transfer_encoding_header, transfer_encoding, status = create_transfer_encoding_header(request_parsed_data)
                if status == OK:
                    response_headers += transfer_encoding_header
                else:
                    transfer_encoding = None
                    content_lenth_header, status = create_content_lenth_header(path)
                    response_headers += content_lenth_header

            if status == OK:
                status_line = create_status_line(metadata, status)
                message = status_line + response_headers + CRLF
                payload = apply_transformations(content_encoding, transfer_encoding, path)
                while user.Stamp != stamp:
                    pass

                connection_socket.send(message.encode())
                connection_socket.send(payload)
                user.Stamp += 1
        if status == 400 :
                close_connection = handle_error(user, status, connection_socket, metadata, stamp, request_parsed_data)
        if not close_connection :
            user.accept_next()
    except socket.error as msg:
        close_connection = True
    if close_connection :
        user.close_connection(connection_socket)

def save_payload(payload, path) :
    status = OK
    if not payload :
        if os.path.isfile(path) :
            with open(path, 'ab') as file :
                file.write(payload)
        else :
            with open(path, 'wb') as file :
                file.write(payload)
    else :
        status = 400
    return status
