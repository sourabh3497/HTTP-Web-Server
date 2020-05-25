import handle_users
from create_headers import *
from handle_error import *
import re, socket, base64

OK = 000
CRLF = '\r\n'

def handle_delete(user, request_parsed_data, metadata, connection_socket, stamp):
    global OK, CRLF
    status = OK
    status_line = ''
    headers = request_parsed_data['headers']

    close_connection = check_connection(request_parsed_data)
    #HANDLING INCOMING DATA
    if 'Authorization' in headers :
        try :
            status = check_authorization(headers['Authorization'], metadata)
            if status == OK :
                path, status = get_path(request_parsed_data, metadata)
                if status == OK :
                    if not os.access(path, os.W_OK) :
                        status = 405
                if (status == OK) :
                    status = delete_file(path)
                else :
                    status = 400

                if status == OK :
                    response_headers = ''
                    payload = ''
                    message = ''
                    content_encoding, transfer_encoding = '', ''
                    path = 'delete.html'

                    status = check_conditions(request_parsed_data, path)
                    if status == OK :
                        date_header = create_date_header()
                        response_headers += date_header

                        content_type_header, status = create_content_type_header(request_parsed_data, path)
                        if status == OK :
                            response_headers += content_type_header

                        if status == OK :
                            transfer_encoding_header, transfer_encoding, status = create_transfer_encoding_header(request_parsed_data)
                            if status == OK :
                                response_headers += transfer_encoding_header
                            else :
                                transfer_encoding = None
                                content_lenth_header, status = create_content_lenth_header(path)
                                response_headers += content_lenth_header
                        if status == OK :
                            status_line = create_status_line(metadata, status)
                            message = status_line + response_headers + CRLF
                            payload = apply_transformations(content_encoding, transfer_encoding, path)
                            while user.Stamp != stamp :
                                pass
                            connection_socket.send(message.encode())
                            connection_socket.send(payload)
                            user.Stamp += 1
            else :
                status = 400
        except socket.error as msg :
            close_connection = True
    else :
        status = 401
    if status != OK :
        close_connection = handle_error(user, status, connection_socket, metadata, stamp, request_parsed_data)
    if not close_connection :
        user.accept_next()
    if close_connection :
        user.close_connection(connection_socket)

def delete_file(path) :
    status = OK
    os.remove(path)
    return status

def check_authorization(credentials, metadata) :
    status = OK
    user_pwd = base64.b64decode(credentials)
    user_pwd = user_pwd.decode()
    if user_pwd != metadata['authorization'] :
        status = 400
    return status
