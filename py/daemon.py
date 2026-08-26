#!/usr/bin/env python

import sqlite3
import ipaddress
from datetime import date, datetime, timezone
import os
import signal
import socket
from pathlib import Path
import json
from nftables import Nftables 
from collections.abc import Iterable

#create table and its internal content
def create_nft_table():
    nft = Nftables()

    #rc, output, error = nft.cmd("add table inet ipban { flags owner; }")
    rc, output, error = nft.cmd("add table inet ipban")
    rc, output, error = nft.cmd(f"add set inet ipban banned_ipv4 {{ type ipv4_addr; }}")
    rc, output, error = nft.cmd(f"add set inet ipban banned_ipv6 {{ type ipv6_addr; }}")

    rc, output, error = nft.cmd("add chain inet ipban in_ban { type filter hook input priority filter; }")
    
    rc, output, error = nft.cmd("add rule inet ipban in_ban ip saddr @banned_ipv4 drop")
    rc, output, error = nft.cmd("add rule inet ipban in_ban ip6 saddr @banned_ipv6 drop")

def destroy_nft_table():
    nft = Nftables()
    rc, output, error = nft.cmd("destroy table inet ipban")

#delete old table, create new, and fill with ip's
def flush_nft(ips : Iterable[ipaddress.IPv4Address]):
    nft = Nftables()
    ips_str = ""
    for ip in ips:
        ips_str += f"{str(ip)}, "
    ips_str = ips_str[:-2]
    if ips_str == "":
        return
    rc, output, error = nft.cmd("destroy set inet ipban banned_ipv4")
    rc, output, error = nft.cmd(f"""add set inet ipban banned_ipv4 {{type ipv4_addr; 
    elements = {{ {ips_str} }}; }}""")

#add list of ips to set in nft
def add_to_end_nft(ips: Iterable[ipaddress.IPv4Address]):
    nft = Nftables()
    ips_str = ""
    for ip in ips:
        ips_str += f"{str(ip)}, "
    ips_str = ips_str[:-2]
    if ips_str == "":
        return
    rc, output, error = nft.cmd(f"add element inet ipban banned_ipv4 {{ {ips_str} }}")

def init_nft(sql_conn: sqlite3.Connection):
    rows = sql_conn.execute("""SELECT ip FROM banned
    """).fetchall()
    flush_nft([row[0] for row in rows])

#add selected ip to db table banned 
def make_ban(sql_conn: sqlite3.Connection, ip: ipaddress.IPv4Address, remark = "", reason = "") -> bool:
    #checking if ip is already banned
    row = sql_conn.execute(f"""SELECT id FROM {ban_t_name}
    WHERE ip = ? LIMIT 1""", (str(ip),)).fetchone()
    print(row)
    
    if row is not None:
        return False    #already banned
    
    ban_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql_conn.execute(f"""INSERT INTO {ban_t_name} (ban_time,ip,remark,reason) VALUES (?, ?, ?, ?)""",
                 (str(ban_time), str(ip), remark, reason))
    sql_conn.commit()
    return True

#what to do in case of req_type=="action"
#TODO: protect from situation: ban "1.1.1.1", uban "1.1.1.1"
def action(sql_conn: sqlite3.Connection, conn: socket.socket, data: str):
    data = data[data.find('\n')+1:] #strip req_type
    data_json = json.loads(data)
    
    ips_to_ban = list()
    for ip,creds in data_json["ban"].items():
        ip_addr = ipaddress.IPv4Address(ip)
        remark = creds["remark"]
        reason = creds["reason"]
        make_ban(sql_conn, ip_addr, remark, reason)
        ips_to_ban.append(ip)

    for ip, creds in data_json["uban"].items():
        print("Not implemented yet")
        break
    add_to_end_nft(ips_to_ban)

def list_ips(sql_conn: sqlite3.Connection, conn: socket.socket, data: str):
    data = data[data.find('\n')+1:] #strip req_type


def recv_all(conn: socket.socket) -> bytes:
    chunks = []

    while True:
        data = conn.recv(4096)

        if not data:
            break
        chunks.append(data)
    return b"".join(chunks)


#initilise UNIX socket and do someting like http handler
def run_server(socket_path: Path, sql_conn: sqlite3.Connection):
    if os.path.exists(socket_path):
        os.unlink(socket_path)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    server.bind(socket_path.as_posix())
    server.listen()

    try:
        while True:
            conn,_ = server.accept()

            try:
                data=recv_all(conn)
                if not data:
                    continue
                
                data = data.decode()
                req_type = data.split('\n')[0]
                
                match req_type:
                    case "action":
                        action(sql_conn, conn, data)
                    case "list":
                        list_ips(sql_conn, conn, data)


            finally:
                conn.close()
    finally:
        server.close()
        if os.path.exists(socket_path):
            os.unlink(socket_path)


def stop_handler(sugnum, frame):
    destroy_nft_table()
    os._exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)
    sql_conn = sqlite3.connect("/var/lib/ipban/db.file")
    ban_t_name="banned"
    sql_conn.execute(f"""CREATE TABLE IF NOT EXISTS {ban_t_name} 
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                ban_time TEXT NOT NULL,
                ip TEXT NOT NULL,
                remark TEXT,
                reason TEXT)""")

    create_nft_table()
    init_nft(sql_conn)
    #flush_nft([ ipaddress.IPv4Address("123.134.124.1"), ipaddress.IPv4Address("8.8.8.8")])
    
    sock_path = Path("/run/ipban/ipban.sock")
    sock_path.parent.mkdir(parents=True,exist_ok=True)
    run_server(sock_path, sql_conn)
    destroy_nft_table()
