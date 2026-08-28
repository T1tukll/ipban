#!/usr/bin/env python

from enum import unique
import ipaddress
import os
import signal
import socket
import json
from collections.abc import Iterable
import argparse

def conctruct_json(ban_list: Iterable[ipaddress.IPv4Address] | Iterable[ipaddress.IPv6Address],
                   uban_list: Iterable[ipaddress.IPv4Address] | Iterable[ipaddress.IPv6Address],)-> str:
    json_map = {"ban": {}, "uban": {} }
    for ip in ban_list:
        json_map["ban"][str(ip)] = {
            "remark": "",
            "reason": ""
        }
    for ip in uban_list:
        json_map["uban"][str(ip)] = {
            "reason": ""
        }

    return json.dumps(json_map)

def recv_all(conn: socket.socket) -> bytes:
    chunks = []

    while True:
        data = conn.recv(4096)

        if not data:
            break
        chunks.append(data)
    return b"".join(chunks)

def req_list(client: socket.socket):
    client.sendall(b"list")
    client.shutdown(socket.SHUT_WR)
    
    daemon_responce = recv_all(client).decode()
    out_dict = json.loads(daemon_responce)
    print(json.dumps(out_dict, indent=2))

def req_action(sock_path:socket.socket, args):
    conflicts_ban_uban = False
    if args.ban != None and args.uban != None:
        conflicts_ban_uban = not (set(args.ban).isdisjoint(args.uban))
    if conflicts_ban_uban:
        print("--ban and --uban must not contain common element(s)")
        exit(1)
    
    if args.ban != None:
        ip_to_ban = [ipaddress.IPv4Address(ip) for ip in args.ban]
    else:
        ip_to_ban = []
    
    if args.uban != None:
        ip_to_uban = [ipaddress.IPv4Address(ip) for ip in args.uban]
    else:
        ip_to_uban = []
    
    request = "action\n" + conctruct_json(ip_to_ban, ip_to_uban)

    socket_path = "/run/ipban/ipban.sock"

    client.sendall(request.encode())
    client.shutdown(socket.SHUT_WR)
    print(client.recv(4096).decode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b","--ban",nargs="+",type=str,metavar="ip",
                        help="ban ip's")
    parser.add_argument("-u", "--uban", nargs="+", type=str,metavar="ip",
                        help="unban ip's")
    parser.add_argument("-l", "--list", action="store_true")
    args = parser.parse_args()
    

    socket_path = "/run/ipban/ipban.sock"
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(socket_path)
    if args.ban != None or args.uban != None:
        req_action(client,args)
    if args.list:
        req_list(client)
