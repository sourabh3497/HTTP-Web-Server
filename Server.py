import threading
from handle_users import *
import json, copy, configparser
from socket import *

class Server :
    def __init__(self, port = 2001) :
        self.port = port
        self.sock = socket(AF_INET,SOCK_STREAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.bind(('', self.port))
        self.sock.listen(5)
        self.terminate = True
        self.users = []
        self.metadata = self.load_metadata()
        self.create_config_file()
        self.load_config_file()
        print('HTTP-SERVER Is Ready')

    def get_users(self):
        return self.users

    def add_user(self, tuple):
        self.users.append(tuple)

    def remove_user(self, user):
        index = 0
        for i in range(len(self.users)) :
            if self.users[i][0] == user :
                index = i
                break
        self.users.pop(index)

    def shutdown(self):
        self.sock.shutdown(SHUT_RDWR)
        self.terminate = False
        users = copy.copy(self.get_users())
        for user in users :
            user[0].close_connection(user[1])
            user[2].join()

    def run(self) :
        try :
            while True and self.terminate :
                connection_socket, addr = self.sock.accept()
                if self.terminate :
                    if len(self.get_users()) <= self.max_connections :
                        user = Handle_User(self)
                        user_t = threading.Thread(target = user.handle_user, args = (self, connection_socket, addr))
                        user_t.start()
                        self.add_user((user, connection_socket, user_t, addr))
                    else :
                        status = 500        #server unavailable
                        handle_error.handle_error(status, connection_socket, self.metadata)
        except :
            pass

    def load_metadata(self, file_path = 'metadata.json'):
        with open(file_path) as infile:
            metadata = json.load(infile)
        return metadata

    def get_metadata(self):
        return self.metadata

    def create_config_file(self) :
        config = configparser.ConfigParser()
        config['SERVER'] = {'DocumentRoot': os.getcwd() + '/index',
                            'log file name': 'server_log.log',
                            'max simultaneous connections': '30'}
        with open('server.ini', 'w') as configfile:
            config.write(configfile)

    def load_config_file(self) :
        config = configparser.ConfigParser()
        config.read('server.ini')

        self.max_connections = int(config['SERVER']['max simultaneous connections'])
        self.metadata['DocumentRoot'] = config['SERVER']['documentroot']
        self.metadata['LOG_FILENAME'] = config['SERVER']['log file name']

server = Server()
t = threading.Thread(target = server.run)
t.start()
flag = True

while flag :
    action = input()
    if action == 'stop' :
        server.shutdown()
        t.join()
        flag = False
    elif action == 'restart' :
        server.shutdown()
        t.join()
        server = Server()
        t = threading.Thread(target = server.run)
        t.start()
print('SUCCESS')
