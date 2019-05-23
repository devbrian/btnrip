import requests


class Deluge:
    cookies = None
    request_id = 0
    host = ""
    port = ""
    key = ""

    def __init__(self, host, port, key):
        self.host = host
        self.port = port
        self.key = key
        assert self.send_request('auth.login', [key]), 'Unable to log in. Check password.'

    def send_request(self, method, params=None):
        self.request_id += 1

        try:

            response = requests.post(
                'http://' + self.host + ':' + self.port + '/json',
                json={'id': self.request_id, 'method': method, 'params': params or []},
                cookies=self.cookies)

        except requests.exceptions.ConnectionError:
            raise Exception('WebUI seems to be unavailable. Run deluge-web or enable WebUI plugin using other thin client.')

        data = response.json()

        error = data.get('error')

        if error:
            msg = error['message']

            if msg == 'Unknown method':
                msg += '. Check WebAPI is enabled.'

            raise Exception('API response: %s' % msg)

        self.cookies = response.cookies

        return data['result']

    def get_torrents(self):
        vals = ["seeding_time", "save_path", "is_finished", "name", "hash"]
        #vals = []
        r = self.send_request('core.get_torrents_status', [[], vals])
        return r

    def remove_torrents(self, hash):
        print(hash)
        vals = [hash, False]
        r = self.send_request('core.remove_torrent', vals)
        return r
