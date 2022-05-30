import datetime
import os
from flask.views import MethodView
from flask import request, abort, render_template, render_template_string
import auth


class FileSystem:
    def __init__(self, root):
        # super().__init__()
        self.fsroot = root

    def dav2fs(self, base, obj=None):
        ret = os.path.join(self.fsroot, base)
        if obj:
            return os.path.join(ret, base)
        return ret

    def isdir(self, path):
        return os.path.isdir(path)

    def listdir(self, path):
        fspath = self.dav2fs(path)
        return os.listdir(fspath)

    def get_prop(self, base, obj):
        isdir = self.isdir(self.dav2fs(base, obj))
        info = os.stat(self.dav2fs(base, obj))
        dt_create = datetime.datetime.fromtimestamp(info.st_ctime).strftime("%a, %d %b %Y %H:%M:%S GMT")
        dt_modify = datetime.datetime.fromtimestamp(info.st_mtime).strftime("%a, %d %b %Y %H:%M:%S GMT")
        href = '/' + base + obj
        if isdir and not href.endswith('/'):
            href += '/'
        return {'href': href, 'displayname': obj, 'isdir': isdir, 'creationdate': dt_create,
                'getlastmodified': dt_modify, 'getcontentlength': info.st_size}


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
    # def dispatch_request(self, *args, **kwargs):
    #     meth = getattr(self, request.method.lower(), None)
    #
    #     # If the request method is HEAD and we don't have a handler for it
    #     # retry with GET.
    #     if meth is None and request.method == "HEAD":
    #         meth = getattr(self, "get", None)
    #     if 'path' not in kwargs.keys():
    #         kwargs['path'] = ''
    #     assert meth is not None, f"Unimplemented method {request.method!r}"
    #     return meth(*args, **kwargs)

    def get(self, path):
        begin = 0
        end = None
        if 'Range' in request.headers:
            r0, r1 = request.headers['Range'].split("-")
            if r0:
                begin = int(r0)
            if r1:
                end = int(r1)
        return "test page.", 200, {}

    def head(self, path):
        pass

    def options(self, path):
        headers = {'DAV': '1,2', 'MS-Author-Via': 'DAV', 'Allow': ','.join(self.methods)}
        return '', 200, headers

    def propfind(self, path):
        d = request.headers.get('Depth', 'infinity')
        depth = int(d) if d.isdigit() else 1  # max depth
        if self.ALLOW_PROPFIND_INFINITY or depth <= 1:
            body = request.data
            print(body)
            l = self.find(path, depth, body)
            headers = {'Content-Type': 'application/xml; charset="utf-8"'}
            res = render_template('prop.xml', objects=l).encode('utf-8')
            print(res)
            return res, 207, headers
        else:
            abort(403)  # depth of infinity are not allowed

    def find(self, path, depth, body):
        if b'allprop' in body:
            pass
        elif b'propname' in body:
            pass
        else:
            pass
        ret = [self.filesystem.get_prop(path, '')]
        if 0 < depth:
            l = self.filesystem.listdir(path)
            for x in l:
                ret.append(self.filesystem.get_prop(path, x))
        return ret
