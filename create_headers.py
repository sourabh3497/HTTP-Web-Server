import time
import os, re
import encoding_decoding
import magic

OK = 000
NOT_APPLICABLE = -1
CRLF = '\r\n'
DEFAULT_PATH = ''


def create_date_header():
    global CRLF
    date_header = 'Date:' + get_date() + CRLF
    return date_header


def get_date():
    IMF_Fixdate = ''
    t = time.ctime()
    segment = t.split(" ")
    segment[0] = segment[0] + ","
    swap(segment[1], segment[2])
    swap(segment[3], segment[4])
    IMF_Fixdate = " ".join(segment)
    IMF_Fixdate += " GMT"
    return IMF_Fixdate


def swap(first, second):
    temp = first
    first = second
    second = temp


def get_path(request_parsed_data, metadata):
    global DEFAULT_PATH
    status = OK
    path = DEFAULT_PATH
    file_pattern = r'/.*[/.]*[^/]$'
    directory_pattern = r'/[/.]*/$'
    target_resource, content_location = '', ''

    headers = request_parsed_data['headers']
    target_resource = request_parsed_data['target_resource']
    if 'Content-Location' in headers:
        content_location = headers['Content-Location']

    if re.match(file_pattern, target_resource):
        path += target_resource
    elif re.match(directory_pattern, target_resource):
        if content_location:
            path += target_resource + content_location
            if not re.match(file_pattern, path):
                status = 400
        else:
            status = 400
    else:
        status = 400

    if (status == OK):
        method = request_parsed_data['method']
        if (method in ('GET', 'HEAD', 'DELETE', 'OPTIONS')):
            if not os.path.exists(path):
                status = 400
        elif method in ('POST', 'PUT'):
            if not os.path.exists(path):
                try:
                    with open(path, 'w') as file:
                        status = 201
                except:
                    status = 400
    return path, status


def check_conditions(request_parsed_data, path):
    return OK


def get_payload(request_parsed_data, connection_socket):
    global OK
    payload = None
    status = OK
    headers = request_parsed_data['headers']
    '''
    if 'Transfer-Encoding' in headers :
        transfer_encoding = headers['Transfer-Encoding']
        if 'chunked' in transfer_encoding[-1] :
            payload, status = encoding_decoding.chunk_decoder(connection_socket)
        else :
            status = 400
    '''
    if 'Content-Length' in headers:
        content_length = headers['Content-Length']
        if content_length:
            chunk_size = 256
            if content_length >= 256:
                payload = connection_socket.recv(chunk_size)
                content_length -= chunk_size
            else:
                payload = connection_socket.recv(content_length)
                content_length = 0
            while content_length >= 256:
                payload += connection_socket.recv(chunk_size)
                content_length -= chunk_size
            payload += connection_socket.recv(content_length)
    return payload, status


def create_content_type_header(request_parsed_data, path = DEFAULT_PATH):
    global OK
    content_type_header = ''
    status = OK
    headers = request_parsed_data['headers']
    mime = magic.Magic(mime=True)
    content_type = mime.from_file(path)
    if (content_type) and (content_type.find('/') != -1):
        media_type, media_subtype = content_type.split('/')
        if 'Accept' in headers:
            accept_encodings = headers['Accept']
            if media_type in accept_encodings:
                media_subtypes = accept_encodings[media_type]
                if (media_subtype in media_subtypes) or ('*' in media_subtypes):
                    content_type_header = 'Content-Type:' + content_type + CRLF
            elif ('*' in accept_encodings):
                content_type_header = 'Content-Type:' + content_type + CRLF
        else:
            content_type_header = 'Content-Type:' + content_type + CRLF
    else:
        status = 400

    return content_type_header, status


def create_transfer_encoding_header(request_parsed_data):
    global CRLF, OK, NOT_APPLICABLE
    transfer_encoding_header = ''
    status = OK
    transfer_encoding = ''
    headers = request_parsed_data['headers']

    if 'TE' in headers:
        values = headers['TE']
        if 'chunked' in values:
            transfer_encoding = 'chunked'
        else:
            status = NOT_APPLICABLE
    else:
        transfer_encoding = 'chunked'
    transfer_encoding_header = 'Transfer-Encoding:' + transfer_encoding + CRLF

    return transfer_encoding_header, transfer_encoding, status


def create_content_lenth_header(path=None):
    global CRLF
    status = OK
    content_lenth_header = ''
    size = 0
    if path:
        size = os.path.getsize(path)
    content_lenth_header = 'Content-Length: ' + str(size) + CRLF
    return content_lenth_header, status


def apply_transformations(content_encoding, transfer_encoding, path = DEFAULT_PATH):
    payload = ''
    if content_encoding:
        # apply content_encoding
        pass
    elif transfer_encoding:
        payload = encoding_decoding.chunk_encoder(path)
    else:
        file = open(path, 'rb')
        payload = file.read()
    return payload


def create_status_line(metadata, status):
    global CRLF
    if status == OK:
        status = 200
    status_line = ''
    status_line += metadata['http_version'] + ' ' + str(status) + ' ' + 'OK' + CRLF
    return status_line


def create_allow_header(path):
    global CRLF
    non_text_types = ['image', 'audio', 'video']
    allow_header = 'Allow:'
    status = OK

    mime = magic.Magic(mime=True)
    content_type = mime.from_file(path)
    media_type, media_subtype = content_type.split('/')

    if media_type in non_text_types:
        allow_header += 'GET, HEAD'
    else:
        allow_header += 'GET, HEAD, PUT, POST, DELETE'
    allow_header += CRLF
    return allow_header, status


def create_www_authenticate_header():
    global CRLF
    authenticate_header = 'WWW-Authenticate: Basic' + CRLF
    return authenticate_header


def check_connection(request_parsed_data):
    close_connection = False
    connection = ''
    http_version = request_parsed_data['http_version']
    headers = request_parsed_data['headers']
    if 'Connection' in headers:
        connection = headers['Connection']
    if connection == 'close':
        close_connection = True
    return close_connection
