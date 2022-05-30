from flask import Flask
import view

app = Flask(__name__)


# ガター内の緑色のボタンを押すとスクリプトを実行します。
if __name__ == '__main__':
    # app.register_blueprint(dav.bp)
    # app.add_url_rule('/', view_func=DavView.DavView.as_view('view1'))
    davview = view.DavView.as_view('view0')
    app.add_url_rule('/', defaults={'path': ''}, view_func=davview)
    app.add_url_rule('/<path>', view_func=davview)

    app.run(debug=True)
