from time import sleep
from sqlalchemy import create_engine
import requests
import json
import datetime

from qbt_api import QBT

db_connect = create_engine('sqlite:///btn.db')

server_list = {
    0: ("http://XXX:5002", "KEY"),
    1: ("http://YYY:5002", "KEY")
}


def add_torrent(server_info, url, name):
    j = {"url": url, "name": name}
    j = json.dumps(j)
    inner_r = requests.post(
        server_info[0] + "/addtorrent",
        headers={"key": server_info[1], "Content-Type": "application/json"},
        json=j
    )
    return inner_r


def del_torrent(server_info, hash):
    j = {"hash": hash}
    j = json.dumps(j)
    inner_r = requests.post(
        server_info[0] + "/deltorrent",
        headers={"key": server_info[1], "Content-Type": "application/json"},
        json=j
    )
    return inner_r


if __name__ == '__main__':
    while True:
        finished = []
        for server_id in server_list:
            server_info = server_list[server_id]
            r = requests.get(
                server_info[0] + "/deluge/getTorrents",
                headers={"key": server_info[1]}
            )
            inter_counter = 0
            for x, y in r.json().items():
                if not y["is_finished"]:
                    inter_counter += 1
                else:
                    if str(y["save_path"]).__contains__("seed"):
                        del_torrent(server_info, y["hash"])
                        with db_connect.connect() as con:
                            dt = datetime.datetime.now().strftime("%x %H:%M")
                            statement = """
UPDATE Torrents SET DownloadMoved = 1 WHERE hash = '{}'
                         """.format(
                                y["hash"]
                            )
                            con.execute(statement)

            while inter_counter < 125 and server_id == 0:
                torrent_id = None
                with db_connect.connect() as con:
                    statement = """SELECT A.TorrentID
from BTN A
LEFT JOIN Torrents B
on A.TorrentID = B.TorrentID
where B.TorrentID IS NULL
LIMIT 1"""
                    df = con.execute(statement)
                    torrent_id = str(df.fetchone()[0])
                    df.close()

                url = "https://broadcasthe.net/torrents.php?action=download&id="+torrent_id+"&authkey={}&torrent_pass={}"
                resp = add_torrent(server_info, url, torrent_id)
                name = str(resp.text).replace("\"", "").replace("\n", "")
                hash_n = ""
                trys = 0
                found = False
                sleep(10)
                while trys < 3 and not found:
                    inner_r = requests.get(
                        server_info[0] + "/deluge/getTorrents",
                        headers={"key": server_info[1]}
                    )
                    for x, y in inner_r.json().items():
                        if y["name"] == name:
                            hash_n = x
                            found = True
                            break
                    trys += 1
                    if not found:
                        sleep(10)
                if resp.status_code == 200:
                    with db_connect.connect() as con:
                        dt = datetime.datetime.now().strftime("%x %H:%M")
                        statement = """
INSERT INTO Torrents(TorrentID, TorrentName, hash, Server, DownloadChecked,
 DownloadMoved, AddTime) VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}')
 """.format(
                            torrent_id,
                            name.replace("'", "''"),
                            hash_n,
                            server_id,
                            0,
                            0,
                            dt
                        )
                        con.execute(statement)
                        inter_counter += 1

            with db_connect.connect() as con:
                statement = """
SELECT * FROM Torrents
where DownloadMoved = 1
"""
                df = con.execute(statement)
                rows = df.fetchall()
                ids = []
                for row in rows:
                    downloaded = row[5]
                    id = row[0]
                    name = row[1]
                    hash = row[2]
                    if downloaded == 1:
                        ids.append((id, hash, name))
                df.close()
                qbt = QBT()
                torrents = qbt.get_torrents()
                qbt_names = []
                for x in torrents:
                    qbt_names.append((x["name"]))

                for t_id in ids:
                    if t_id[2] not in qbt_names:
                        print("Calling add_torrent - " + str(t_id))
                        qbt.add_torrent(t_id[0])
        print("Sleeping for 12 minutes..")
        sleep(600)
