from flask_httpauth import HTTPDigestAuth, HTTPAuth


class NoAuth(HTTPAuth):
    def authenticate(self, auth, stored_password):
        return True


auth = NoAuth() # HTTPDigestAuth()


@auth.get_password
def get_password(username):
    return "1234"