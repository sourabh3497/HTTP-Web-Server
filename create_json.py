import json, socket

def save_metadata(file_path = 'metadata.json') :
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_addr = s.getsockname()[0]
    port = str(get_free_tcp_port())

    metadata = {
    'protocol': 'HTTP',
    'host': ip_addr,
    'port': '2001',
    'http_version': 'HTTP/1.1',
    'request-headers': ['Connection','Date','Transfer-Encoding','Accept','Accept-Encoding','Host','TE','Content-Encoding','Content-Length','Content-Type', 'Authorization'],
    'methods': ['GET', 'HEAD', 'PUT', 'POST', 'DELETE', 'OPTIONS'],
    'Connection': ['close', 'keep-alive'],
    'Transfer-Encoding': ['chunked', 'compress', 'deflate', 'gzip'],
    'TE': ['chunked', 'compress', 'deflate', 'gzip'],
    'Content-Encoding': ['compress', 'deflate', 'gzip'],
    'Content-Type': ['text', 'image', 'audio', 'video'],
    'authorization': 'SERVER:3497'
    }
    with open(file_path, 'w') as outfile:
        json.dump(metadata, outfile)

def get_free_tcp_port():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(('', 0))
    addr, port = tcp.getsockname()
    tcp.close()
    return port

save_metadata()