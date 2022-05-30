from flask.views import MethodView
from flask import request, abort, render_template, render_template_string
import os

class DavView(MethodView):
    methods = ['HEAD', 'GET', 'PROPFIND', 'OPTIONS']
        # , 'PROPPATCH', 'MKCOL', 'DELETE',
        #        'COPY', 'MOVE', 'PUT'

    def dav2fs(self, path):
        return self.fsroot + path

    def __init__(self):
        super().__init__()
        self.ALLOW_PROPFIND_INFINITY = False
        self.fsroot = './venv/'

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)

        # If the request method is HEAD and we don't have a handler for it
        # retry with GET.
        if meth is None and request.method == "HEAD":
            meth = getattr(self, "get", None)
        if 'path' not in kwargs.keys():
            kwargs['path'] = ''
        assert meth is not None, f"Unimplemented method {request.method!r}"
        return meth(*args, **kwargs)

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
            return res, 200, headers
        else:
            abort(403)  # depth of infinity are not allowed

    def find(self, path, depth, body):
        if b'allprop' in body:
            pass
        elif b'propname' in body:
            pass
        else:
            pass
        l = os.listdir(self.dav2fs(path))
        ret = []
        for x in l:
            isdir = os.path.isdir(self.dav2fs(x))
            href = 'http://localhost:5000/' + path + x + ('/' if isdir else '')
            ret.append({'href': href, 'displayname': x, 'isdir': isdir})
        return ret
