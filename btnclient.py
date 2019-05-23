import urllib.request
from functools import wraps

from flask import Flask, request
from flask_restful import Resource, Api, abort
from flask_cors import CORS

import json
import configparser
import torrent_parser as tp

import bencoding
import hashlib

from deluge_api import Deluge

app = Flask(__name__)
api = Api(app)
CORS(app)
config = configparser.ConfigParser()
config.read('config.ini')
client_config = config["CLIENT"]

deluge = Deluge(client_config["host"], client_config["port"], client_config["pass"])


def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('key') and request.headers.get('key') == client_config["api_key"]:
            return view_function(*args, **kwargs)
        else:
            abort(401)
    return decorated_function


class DelugeApp(Resource):
    @require_appkey
    def get(self):
        r = deluge.get_torrents()
        return r


class AddTorrents(Resource):
    @require_appkey
    def post(self):
        content = json.loads(request.get_json(silent=True))
        url = str(content['url']).format(client_config["auth_key"], client_config["torrent_pass"])
        name = content['name']
        print(name)
        store_url = client_config["watch_folder"] + str(name) + ".torrent"
        urllib.request.urlretrieve(url, store_url)
        data = tp.parse_torrent_file(store_url)
        return str(data["info"]["name"])


class RemoveTorrents(Resource):
    @require_appkey
    def post(self):
        content = json.loads(request.get_json(silent=True))
        hash = content['hash']
        r = deluge.remove_torrents(hash)
        return r


api.add_resource(DelugeApp, '/deluge/getTorrents')
api.add_resource(AddTorrents, '/addtorrent')
api.add_resource(RemoveTorrents, '/deltorrent')

if __name__ == '__main__':
    app.run(port=5002, host="0.0.0.0")
