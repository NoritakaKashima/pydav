from flask import Flask, Blueprint
import view

bp = Blueprint('simple_page', __name__)


@bp.route('/')
def index():
    return show('/')


@bp.route('/<path>')
def show(path):
    return "test page.", 200, {}

