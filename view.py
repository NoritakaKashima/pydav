import datetime
import gzip
import os

import flask
from flask.views import MethodView
from flask import request, abort, render_template, render_template_string
import auth
import re

types = {
    '.txt': 'text/plain',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
}


class FileSystem:
    def __init__(self, root):
        # super().__init__()
        self.fsroot = root

    def dav2fs(self, base, obj=None):
        ret = os.path.join(self.fsroot, base)
        if os.path.sep == '\\':
            ret = ret.replace('/', '\\')
        #ret = os.path.normpath(ret)
        if obj:
            return os.path.join(ret, obj)
        return ret

    def isfile(self, path):
        return os.path.isfile(self.dav2fs(path))

    def isdir(self, path):
        return os.path.isdir(self.dav2fs(path))

    def listdir(self, path):
        fspath = self.dav2fs(path)
        return os.listdir(fspath)

    def get_prop(self, base, obj):
        fspath = self.dav2fs(base, obj)
        isdir = os.path.isdir(fspath)
        info = os.stat(fspath)
        name = obj if obj else os.path.basename(base)
        dt_create = datetime.datetime.fromtimestamp(info.st_ctime)
        dt_modify = datetime.datetime.fromtimestamp(info.st_mtime)
        # href = '/' + base + obj
        href = 'http://localhost:5000/' + base + obj
        if isdir and not href.endswith('/'):
            href += '/'
        b, ext = os.path.splitext(fspath)
        type = ''
        if ext in types:
            type = types[ext]
        props = {
            'displayname': name,
            'resourcetype': isdir,
            'creationdate': dt_create.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            'getlastmodified': dt_modify.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            'getcontentlength': info.st_size,
            'getetag': dt_modify.strftime("%Y%m%d%H%M%S"),
            'getcontenttype': type}
        return {'href': href, 'props': props, 'prop_keys': list(props.keys())}

    def open(self, path, _range):
        BUFFER_READ = 4096
        fspath = self.dav2fs(path)
        size = os.path.getsize(fspath)
        start = 0
        length = 0
        if _range:
            start = _range[0]
            if _range[1]:
                length = _range[1] - start + 1
            else:
                length = size - start
        else:
            length = size

        def generate():
            with open(fspath, 'rb') as f:
                f.seek(start)
                read = 0
                while not length or read < length:
                    length_to_read = min(length - read, BUFFER_READ) if length else BUFFER_READ
                    d = f.read(length_to_read)
                    if d == 0:
                        break
                    read += length_to_read
                    yield d
        return generate


class DavView(MethodView):
    methods = ['HEAD', 'GET', 'PROPFIND', 'OPTIONS']
        # , 'PROPPATCH', 'MKCOL', 'DELETE',
        #        'COPY', 'MOVE', 'PUT'

    def __init__(self, filesystem):
        super().__init__()
        self.ALLOW_PROPFIND_INFINITY = False
        self.filesystem = filesystem

    @auth.auth.login_required
    def dispatch_request(self, *args, **kwargs):
        return super().dispatch_request(*args, **kwargs)

    def get(self, path):
        if not self.filesystem.isfile(path):
            abort(404)
        _range = None
        if 'Range' in request.headers:
            print(f'Range request: {request.headers["Range"]}')
            r0, r1 = request.headers['Range'].split("-")
            _range = (int(r0), int(r1) if r1 else None)
        stream = self.filesystem.open(path, _range)
        status = 206 if _range else 200
        return flask.Response(stream(), status, headers={}, direct_passthrough=True)

    def head(self, path):
        pass

    def options(self, path):
        headers = {'DAV': '1,2', 'MS-Author-Via': 'DAV', 'Allow': ','.join(self.methods), 'Accept-Ranges': 'bytes'}
        return '', 200, headers

    def propfind(self, path):
        pat = r'<(.+:)?(.+)\s*/>'

        def get_prop(str):
            m = re.match(pat, str)
            if m:
                return m.group(1), m.group(2)
            else:
                return '', ''

        d = request.headers.get('Depth', 'infinity')
        depth = int(d) if d.isdigit() else 1  # max depth
        if self.ALLOW_PROPFIND_INFINITY or depth <= 1:
            body = request.data
            print(f'PROPFIND depth: {depth} url: {request.url} body: {body}')
            param = {'allprop': False}
            if b'allprop' in body:
                param['allprop'] = True
            elif b'propname' in body:
                print('propname')
            else:
                is_propname = False
                props = {}
                for line in body.decode('utf-8').replace('\n', '').split('>'):
                    line += '>'
                    if 'prop>' in line:
                        is_propname = not is_propname
                    elif is_propname:
                        p = get_prop(line)
                        props[p[1]] = 0
                param['props'] = props

            objs = self.find(path, depth, body)
            res = render_template('prop.xml', param=param, objs=objs).encode('utf-8')
            print(res)
            h = {'Content-Type': 'application/xml; charset="utf-8"', 'Accept-Ranges': 'bytes'}
            if 'gzip' in request.accept_encodings and 100 < len(res):
                res = gzip.compress(res)
                h['Content-Encoding'] = 'gzip'
            return res, 207, h
        else:
            abort(403)  # depth of infinity are not allowed

    def find(self, path, depth, body):
        p = self.filesystem.get_prop(path, '')
        ret = [p]
        if p['props']['resourcetype'] and 0 < depth:
            l = self.filesystem.listdir(path)
            for x in l:
                ret.append(self.filesystem.get_prop(path, x))
        return ret
