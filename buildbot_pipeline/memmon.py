"""
socat - UNIX:/tmp/memmon.sock
"""
import sys
import os
import socket
import cmd
import gc
import collections
import threading
import pdb
from types import MappingProxyType

_refs = set()

class Stat:
    def __init__(self, limit = 10):
        self.counts = counts = collections.Counter()
        self.sizes = sizes = collections.Counter()
        self.objects = objects = {}
        self.internal_refs = irefs = set()
        self.total = 0
        self.dicts = dicts = {}

        olist = []
        irefs.add(id(olist))
        for o in gc.get_objects():
            oid = id(o)
            if oid in _refs or o is olist:
                continue

            otype = type(o)
            if otype is type:
                key = str(o)
            else:
                key = 'instance of ' + str(otype)

            if hasattr(o, '__dict__'):
                if type(o.__dict__) is MappingProxyType:
                    dicts[id(gc.get_referents(o.__dict__)[0])] = key
                else:
                    dicts[id(o.__dict__)] = key
            olist.append((oid, key, o))

        for oid, key, o in olist:
            if oid in dicts:
                continue

            try:
                ws = objects[key]
            except KeyError:
                ws = objects[key] = []
                irefs.add(id(ws))

            if len(ws) < limit:
                ws.append(o)

            counts[key] += 1
            sz = sys.getsizeof(o, 0)
            sizes[key] += sz
            self.total += sz

        del olist

    def refs_to(self, obj, depth=0):
        frm = [sys._getframe(i) for i in range(depth+1)]
        result = [it for it in gc.get_referrers(obj) if id(it) not in self.internal_refs and it not in frm]
        del frm
        return result

    def refs_from(self, obj):
        return [it for it in gc.get_referents(obj) if id(it) not in self.internal_refs]

    def resolve(self, obj):
        return self.dicts.get(id(obj), obj)

    def rrefs_to(self, obj, depth=0):
        return [self.resolve(it) for it in self.refs_to(obj, depth+1)]

    def orefs_to(self, obj, depth=0):
        return [self.obj(it) or it for it in self.refs_to(obj, depth+1)]

    def obj(self, dictdata):
        for o in gc.get_referrers(dictdata):
            if hasattr(o, '__dict__') and o.__dict__ is dictdata:
                return o


def create_socket(spath):
    if os.path.exists(spath):
        os.remove(spath)
    s = socket.socket(socket.AF_UNIX)
    s.bind(spath)
    s.listen()
    return s


def snapshot():
    _refs.clear()
    _refs.add(id(_refs))
    for o in gc.get_objects():
        _refs.add(id(o))


class EFile:
    def __init__(self, sock):
        self.sock = sock
        self.buf = ''
        self.f = sock.makefile('r', buffering=1)

    def read(self, size):
        return self.f.read(size)

    def write(self, data):
        return self.sock.sendall(data.encode())

    def flush(self):
        pass

    def readline(self):
        return self.f.readline()


class MyPdb(pdb.Pdb):
    use_rawinput = False


def monitor(fname, in_thread=False):
    if in_thread:
        _t = threading.Thread(target=monitor, args=(fname,), daemon=True)
        _t.start()
        return

    _s = create_socket(fname)

    while True:
        _conn, _addr = _s.accept()
        _f = EFile(_conn)
        _r = MyPdb(stdin=_f, stdout=_f)
        try:
            _r.set_trace()
            _conn.shutdown(socket.SHUT_WR)
        except:
            import traceback
            traceback.print_exc()
        _conn.close()


class Boo:
    class Moo:
        pass

    def __init__(self):
        self.foo = 'FOO' * 1000
        self.moo = Boo.Moo()

    def boo(self):
        pass


def test():
    from pprint import pprint
    # snapshot()
    _data = [Boo() for it in range(1000)]

    # pprint(type(gc.get_referrers(s[0].__dict__)[0]))
    # pprint(type(s[0].__dict__))

    # pprint(stat()[0].most_common(10))
    # pprint(stat()[1]['sizes'].most_common(10))
    s = Stat()
    # refs = gc.get_referrers(obj)
    import pdb
    pdb.set_trace()

if __name__ == '__main__':
    test()
    # monitor('/tmp/memmon.sock')
