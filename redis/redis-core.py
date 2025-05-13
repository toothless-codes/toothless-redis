from gevent import socket
from gevent.pool import Pool
from gevent.server import StreamServer

from collections import namedtuple
from io import BytesIO

class CommandError(Exception):
    pass


class Disconnect(Exception):
    pass

Error = namedtuple('Error', ('message',))

class ProtocolHandler(object):
    def __init__(self):
        self.handlers = {
            '+' : self.handle_simple_string,
            '-' : self.handle_error,
            ':' : self.handle_integer,
            '$' : self.handle_bulk_string,
            '*' : self.handle_array,
        }
    def handle_request(self, socket_file):
        first_byte = socket_file.read(1)
        if not first_byte:
            raise Disconnect()
        try:
            return self.handlers[first_byte](socket_file)
        except KeyError:
            raise CommandError('Bad request')
    def handle_simple_string(self, socket_file):
        return socket_file.readline().rstrip('\r\n')
    
    def handle_error(self, socket_file):
        return Error(socket_file.readline().rstrip('\r\n'))
    
    def handle_integer(self, socket_file):
        return int(socket_file.readline().rstrip('\r\n'))

    def handle_bulk_string(self, socket_file):
        # Read the length prefix (e.g. "5\r\n" → length = 5)
        length = int(socket_file.readline().rstrip('\r\n'))
        # A length of -1 means a NULL bulk string
        if length == -1:
            return None
        # We need to read payload + the final "\r\n"
        length += 2
        # Read that many bytes and strip the trailing CRLF
        return socket_file.read(length)[:-2]

    def handle_array(self, socket_file):
        num_elements = int(socket_file.readline().rstrip('\r\n'))
        return [self.handle_request(socket_file) for _ in range(num_elements)]

    def handle_dict(self, socket_file):
        num_items = int(socket_file.readline().rstrip('\r\n'))
        elements = [self.handle_request(socket_file) for _ in range(num_items * 2)]

        return dict(zip(elements[::2], elements[1::2]))


    def write_response(self, socket_file, data):
        buf = BytesIO()
        self._write(buf, data)
        buf.seek(0)
        socket_file.write(buf.getvalue())
        socket_file.flush()

    def _write(self, buf, data):
        if isinstance (data , str):
            data = data.encode('utf-8')
        if isinstance(data, bytes):
            buf.write('$%s\r\n%s\r\n'%(len(data),data))
        elif isinstance(data,int):
            buf.write(':%s\r\n'% data)
        elif isinstance(data, Error):
            buf.write('-%s\r\n'% data.message)
        elif isinstance(data, (list,tuple)):
            buf.write('*%s\r\n'% len(data))
            for item in data:
                self._write(buf, item)
        elif data is None:
            buf.write('$-1\r\n')
        else:
            raise CommandError('unrecognized type: %s' %type(data))

class server(object):
    def __init__(self, host='127.0.0.1', port=31337, max_clients=64):
        self._pool = Pool(max_clients)
        self._server = StreamServer(
            (host, port),
            self.connection_handler,
            spawn=self._pool)
        self._protocol = ProtocolHandler()
        self._kv = {}
        self.commands = self.get_commands()

    def get_commands(self):
        return{
            'GET': self.get,
            'SET': self.set,
            'DELETE': self.delete,
            'FLUSH': self.flush,
            'MGET': self.mget,
            'MSET': self.mset,
        }
    
    def get(self, key):
        return self._kv.get(key)

    def set(self, key, value):
        self._kv[key]= value
        return 1

    def delete(self, key):
        if key in self._kv:
            del self._kv[key]
        return 1

    def flush(self):
        keylen = len(self._kv)
        self._kv.clear()
        return keylen

    def mget(self, *keys):
        return [self._kv.get(key) for key in keys]

    def mset(self, *items):
        data = zip(items[::2],items[1::2])
        for key, value in data:
            self._kv[key] = value
        return len(data)
    
    def run(self):
        print("Server running...")
        self._server.serve_forever()

    def get_response(self, data):
        if not isinstance(data, list):
            try:
                data = data.split()
            except:
                raise CommandError('request must be a list')
        if not data:
            raise CommandError('request cannot be empty')
        command = data[0].upper()
        if command not in self.commands:
            raise CommandError('unknown command: %s' % command)
        return self.commands[command](*data[1:])

    def connection_handler(self, sock):
        f = sock.makefile('rwb')
        while True:
            try:
                # 1) Read a RESP request → Python object
                req = self._protocol.handle_request(f)
                # 2) Execute it → simple Python result
                res = self.get_response(req)
                # 3) Write it back in RESP
                self._protocol.write_response(f, res)

            except Disconnect:
                break    # client closed connection
            except CommandError as e:
                # Send back a "-ERR message\r\n"
                self._protocol.write_response(f, Error(str(e)))
 
class client(object):

    def get(self, key):
        return self.execute('GET', key)
    def set(self, key, value):
        return self.execute('SET', key, value)
    def delete(self, key):
        return self.execute('DELETE', key)
    def flush(self):
        return self.execute('FLUSH')
    def mget(self, *keys):
        return self.execute('MGET', *keys)
    def mset(self, *items):
        return self.execute('MSET', *items)
    
    def __init__(self, host='127.0.0.1', port=31337):
        self._host = host
        self._port = port
        self._protocol = ProtocolHandler()

    def execute(self, *args):
        s = socket.create_connection((self._host, self._port))
        socket_file = s.makefile('rwb')
        self._protocol.write_response(socket_file, list(args))
        return self._protocol.handle_request(socket_file)



if __name__ == '__main__':
    from gevent import monkey; monkey.patch_all()
    server().run()
