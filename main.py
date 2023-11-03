import socket
import threading

LINE_SEPARATOR = '\r\n'
BUFFER_SIZE = 512

CMD_LOGIN = 'login'
CMD_LOGOUT = 'logout'
CMD_JOIN = 'join'
CMD_SWITCH = 'switch'

class ChatServer:
    server_ip = '127.0.0.1'
    port = 3000

    @classmethod
    def start(cls):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((cls.server_ip, cls.port))
        server.listen(10)
        while True:
            client, client_ip = server.accept()
            print('connected client={}'.format(client_ip))
            thread = threading.Thread(target=msg_process, args=(client, client_ip))
            thread.start()

class User:
    def __init__(self, name, ip, connection) -> None:
        self.name = name
        self.ip = ip
        self.connection = connection
        self.room_name = None

    def now_room(self, room_name):
        self.room_name = room_name
    
    def __str__(self):
        return 'User=[name={0}]'.format(self.name)

    def __eq__(self, other):
        if other == None:
            return False
        return self.name == other.name

class Rooms:
    rooms = {}
    
    @classmethod
    def initialize(cls):
        cls.rooms['room1'] = []
        cls.rooms['room2'] = []
    
    @classmethod
    def exist(cls, name):
        return name in cls.rooms.keys()
    
    @classmethod
    def join_user(cls, name, user):
        cls.rooms[name].append(user)

    @classmethod
    def leave_user(cls, name, user):
        cls.rooms[name].remove(user)

    @classmethod
    def broadcast(cls, user, data):
        for u in cls.rooms[user.room_name]:
            if u.name == user.name:
                continue
            u.connection.send(bytes('<{}>'.format(user.name).encode('utf-8')) + data)

def msg_process(client, client_ip):
    user = None
    while True:
        if user == None:
            client.send(b'please login\n>')
        elif user.room_name == None:
            client.send(b'please join room\n>')
        else:
            msg = '[{0}]>'.format(user.room_name)
            client.send(msg.encode('utf-8'))
        
        data = client.recv(BUFFER_SIZE)
        # byte to string, remove \r\n
        data_str = data.decode('utf-8').strip(LINE_SEPARATOR)
        
        # login
        if data_str.startswith(CMD_LOGIN):
            if user != None:
                # user has already logined.
                continue
            name = data_str.split(' ')[1]
            user = User(name, client_ip, client)
            print('{0} login.'.format(name))
            continue
        # logout
        elif data_str == CMD_LOGOUT:
            if user == None:
                continue
            client.close()
            break
        # join
        elif data_str.startswith(CMD_JOIN):
            if user == None:
                continue
            # check exist room.
            room = data_str.split(' ')[1]
            if not Rooms.exist(room):
                client.send(b"room don't exist.\n>")
                continue
            
            # join room
            Rooms.join_user(room, user)
            user.now_room(room)
            print('{0} joined {1}'.format(user.name, room))
            continue
        # switch
        elif data_str.startswith(CMD_SWITCH):
            if user == None:
                continue
            # check exist room.
            room = data_str.split(' ')[1]
            if not Rooms.exist(room):
                client.send(b"room don't exist\n")
                continue
            
            # leave room
            Rooms.leave_user(user.room_name, user)
            # switch room
            Rooms.join_user(room, user)
            user.now_room(room)
            print('{0} switched {1}'.format(user.name, room))
            continue
        else:
            if user == None or user.room_name == None:
                continue
            Rooms.broadcast(user, data)

if __name__ == '__main__':
    Rooms.initialize()
    ChatServer.start()
    