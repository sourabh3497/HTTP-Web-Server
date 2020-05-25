OK = 000
CRLF = '\r\n'

def chunk_encoder(file_name, chunk_size = 10000) :
    chunked_data = None
    encoding = 'utf-8'
    last_chunk = ('0000' + CRLF).encode()

    file = open(file_name, 'rb')
    data = file.read(chunk_size)
    lenth = (str(hex(len(data))[2:] + CRLF)).encode()
    formatted_data = lenth + data + CRLF.encode()
    chunked_data = formatted_data
    while (len(data) == chunk_size) :
        data = file.read(chunk_size)
        lenth = (str(hex(len(data))[2:] + CRLF)).encode()
        formatted_data = lenth + data + CRLF.encode()
        chunked_data += formatted_data
    chunked_data += last_chunk
    chunked_data += CRLF.encode()
    return chunked_data

def chunk_decoder(connection_socket) :
    payload = None
    status = OK

    return payload, status
