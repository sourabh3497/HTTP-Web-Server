import re
import os
from urllib.parse import *

CRLF = '\r\n'
OK = 000
BAD_REQUEST = 400
DEFAULT_CONNECTION = False

DIGIT = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
ALPHA = ["!", "#", "$", "%", "&", "'", "*", "+", "-", ".", "^", "_", "`", "|", "~"]

# PARSING REQUEST LINE
def parse_requestline(request_line, metadata):
    global DEFAULT_CONNECTION
    status = OK
    method, target_source, http_version = '', '', ''

    method_comp, uri_comp, http_version_comp = request_line.split()
    if method_comp in metadata['methods']: #Check Method Is Implemented
        method = method_comp
        target_source, status = handle_URI(uri_comp, metadata)
        if status == OK:
            http_version, status = handle_HTTP_Version(http_version_comp, metadata)
            if status == OK:
                DEFAULT_CONNECTION = 'close'
    else :
        status = 500
    if status == OK:
        return method, target_source, http_version, status
    else:
        method, target_source, http_version = '', '', ''
        return method, target_source, http_version, status

def handle_HTTP_Version(http_version, metadata):
    status = OK

    protocol, version = http_version.split('/')
    if protocol == 'HTTP':
        version, subversion = version.split('.')
        if (version in DIGIT) and (subversion in DIGIT):
            return http_version, status
    status = BAD_REQUEST
    return http_version, status

def handle_URI(uri_comp, metadata) :
    status = OK
    components = urlparse(uri_comp)
    target_resource = unquote(components.path)
    query = parse_qs(components.query)
    if not target_resource :
        status = 400
    return target_resource, status

#HANDLING HEADERS
def field_value_tokenizer(header_field) :
    functions = {
        'Connection' : parse_connection,
        'Date' : parse_date,
        'Transfer-Encoding' : parse_transfer_encoding,
        'Accept' : parse_accept,
        'Accept-Encoding' : parse_accept_encoding,
        'Expect' : parse_expect,
        'Host' : parse_host,
        'TE' : parse_te,
        'Content-Encoding' : parse_content_encoding,
        'Content-Length' : parse_content_length,
        'Content-Location' : parse_content_location,
        'Content-Type' : parse_content_type,
        'Authorization' : parse_authorization
    }
    return functions[header_field]

def parse_headers(headers, metadata) :
    status = OK
    header_field_pattern = r"[!#$%&'*+-.^_`|~A-Za-z]+:.*"
    field_content_pattern = r"([\x21-\x7E]+[ \t]+)*[\x21-\x7E]+$"
    header_fields = {}

    headers = headers.split(CRLF)[ : -1]
    for header in headers :
        if re.match(header_field_pattern, header) :
            header_separator_index = header.find(':')
            header_field, field_value = header[ : header_separator_index], header[header_separator_index + 1 : ]
            field_value = field_value.strip()
            if re.match(field_content_pattern, field_value) :
                if header_field in metadata['request-headers'] :
                    values, status = field_value_tokenizer(header_field)(field_value, metadata)
                    if status != OK :
                        break
                    header_fields[header_field] = values
                #else :
                    #status code for unsupported type
                #    status = 400
                #    break
            else :
                status = 400
                break
        else :
            status = 400
            break
    return header_fields, status

def parse_connection(field_value, metadata) :
    status = OK
    values = []

    if not field_value :
        status = 400
    else :
        token_separator_index = field_value.find(',')
        if token_separator_index != -1 :
            tokens = field_value.split(',')
        else :
            tokens = [field_value]
        for token in tokens :
            token = token.strip()
            if token :
                if token in metadata['Connection'] :
                    values.append(token)
                else :
                    status = 400
                    break
        if not values :
            status = 400
    return values, status

def parse_date(field_value, metadata) :
    status = OK
    return field_value, status

def parse_transfer_encoding(field_value, metadata) :
    status = OK
    values = []

    if not field_value :
        status = 400
    else :
        coding_separator_index = field_value.find(',')
        if coding_separator_index != -1 :
            transfer_codings = field_value.split(',')
        else :
            transfer_codings = [field_value]
        for transfer_coding in transfer_codings :
            transfer_coding = transfer_coding.strip()
            if transfer_coding :
                if transfer_coding in metadata['Transfer-Encoding'] :
                    values.append(transfer_coding)
                else :
                    status = 400
                    break
        if not values :
            status = 400
    return values, status

def parse_accept_encoding(field_value, metadata) :
    status = OK
    default_q_value = 1.000
    q_value_pattern = r'[qQ]=[01].[0-9][0-9][0-9]'
    values = []

    if field_value :
        codings_present = field_value.find(',')
        if codings_present != -1 :
            codings = field_value.split(',')
        else :
            codings = [field_value]
        for coding in codings :
            coding = coding.strip()
            if coding :
                if coding.find(';') == -1 :
                    values.append({})
                    values[-1]['Content-Coding'] = coding
                    values[-1]['q-value'] = default_q_value
                else :
                    content = field_value.split(';')
                    coding, q_value = content[0], content[1 : ]
                    if len(q_value) == 1 :
                        q_value = q_value[0]
                        coding, q_value = coding.strip(), q_value.strip()
                        if re.match(q_value_pattern, q_value):
                            q, q_value = q_value.split('=')
                            values.append({})
                            values[-1]['Content-Coding'] = coding
                            values[-1]['q-value'] = default_q_value
                        else:
                            status = 400
                            break
    #values.sort() depending on q_value
    return values, status

def parse_expect(field_value, metadata) :
    status = OK
    if field_value.lower() != '100-continue' :
        status = 400
    return field_value, status

def parse_host(field_value, metadata) :
    status = OK
    if field_value.find(':') != -1 :
        host, port = field_value.split(':')
        if (host != metadata['host']) or (port != metadata['port']) :
            status = 400
    elif (field_value != metadata['host']) :
        status = 400
    return field_value, status

def parse_te(field_value, metadata) :
    status = OK
    default_q_value = 1.000
    q_value_pattern = r'[qQ]=[01].[0-9][0-9][0-9]'
    values = []

    if field_value:
        codings_present = field_value.find(',')
        if codings_present != -1:
            codings = field_value.split(',')
        else:
            codings = [field_value]
        for coding in codings:
            coding = coding.strip()
            if coding:
                if coding.find(';') == -1:
                    values.append(coding)
                    #values.append({})
                    #values[-1]['transfer-Coding'] = coding
                    #values[-1]['q-value'] = default_q_value
                else:
                    content = field_value.split(';')
                    coding, q_value = content[0], content[1:]
                    if len(q_value) == 1:
                        q_value = q_value[0]
                        coding, q_value = coding.strip(), q_value.strip()
                        if re.match(q_value_pattern, q_value):
                            q, q_value = q_value.split('=')
                            values.append(coding)
                            #values.append({})
                            #values[-1]['transfer-Coding'] = coding
                            #values[-1]['q-value'] = default_q_value
                        else:
                            status = 400
                            break
    # values.sort() depending on q_value
    return values, status

def parse_content_encoding(field_value, metadata) :
    status = OK
    values = []

    if not field_value:
        status = 400
    else:
        coding_separator_index = field_value.find(',')
        if coding_separator_index != -1:
            content_codings = field_value.split(',')
        else:
            content_codings = [field_value]
        for content_coding in content_codings :
            content_coding = content_coding.strip()
            if content_coding:
                if content_coding in metadata['Content-Encoding']:
                    values.append(content_coding)
                else:
                    status = 400
                    break
        if not values:
            status = 400
    return values, status

def parse_content_length(field_value, metadata) :
    status = OK
    content_lenth_pattern = r"[1-9][0-9]*"
    if re.match(content_lenth_pattern, field_value) :
        return int(field_value), status
    else :
        status = 400
    return field_value, status

def parse_content_location(field_value, metadata) :
    content_location, status = handle_URI(field_value, metadata)
    return field_value, status

def parse_content_type(field_value, metadata) :
    status = OK
    values = {}

    if field_value.find('/') != -1 :
        media_type, component = field_value.split('/')
        media_type = media_type.lower()
        if component.find(';') != -1 :
            content = component.split(';')
            media_subtype, parameters = content[0], content[1 : ]
            media_subtype = media_subtype.rstrip().lower()
        else :
            media_subtype = component.rstrip().lower()
        if media_type in metadata['Content-Type'] :
            #and media_subtype in metadata[media_type]
            values['media-type'] = media_type
            values['media-subtype'] = media_subtype
        else :
            status = 400
    else :
        status = 400
    return values, status

def parse_accept(field_value, metadata) :
    status = OK
    default_q_value = 1.000
    q_value_pattern = r'[qQ]=[01].[0-9][0-9][0-9]'
    values = {}

    if field_value :
        media_types_present = field_value.find(',')
        if media_types_present != -1 :
            media_types = field_value.split(',')
        else :
            media_types = [field_value]
        for type in media_types :
            type = type.strip()
            if type :
                if type.find('/') != -1 :
                    media_type, component = type.split('/')
                    media_type = media_type.lower()
                    if component.find(';') == -1 :
                        media_subtype = component.rstrip().lower()
                        if media_type == '*' and media_subtype != '*':
                            status = 400
                            break
                        if media_type in values :
                            values[media_type].append(media_subtype)
                        else :
                            values[media_type] = [media_subtype]
                        #values[-1]['q-value'] = default_q_value
                    else :
                        content = component.split(';')
                        media_subtype, parameters = content[0], content[1 : ]
                        media_subtype = media_subtype.rstrip().lower()
                        if media_type == '*' and media_subtype != '*':
                            status = 400
                            break
                        if media_type in values:
                            values[media_type].append(media_subtype)
                        else:
                            values[media_type] = [media_subtype]
                        #values[-1]['q-value'] = default_q_value
                        #parse for q-value and parameters
    return values, status

def parse_authorization(field_value, metadata) :
    status = OK
    value = ''

    scheme, value = field_value.strip().split(' ')
    scheme = scheme.strip()
    value = value.strip()
    if scheme != 'Basic' :
        status = 400
    return value, status