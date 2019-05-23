import requests
from requests_toolbelt import MultipartEncoder


class QBT:
    conn = "http://localhost:8080/"

    def get_torrents(self):
        r = requests.get(url=self.conn + "query/torrents")
        r_list = r.json()
        return r_list

    def add_torrent(self, torrent_id):
        print("Adding torrent to QBT - ", torrent_id)
        url = "https://broadcasthe.net/torrents.php?action=download&id={}&authkey=2b15e75ec108db524732432f6935070f&torrent_pass=yq623hobf9dhu0mu49e7v3j9t0xy8ee8".format(
            torrent_id)
        m = MultipartEncoder(
            fields={'urls': url,
                    'skip_checking': 'true'}
        )

        requests.post(self.conn + "command/download", data=m,
                      headers={'Content-Type': m.content_type})