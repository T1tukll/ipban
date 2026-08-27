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
    print(json_map)
    for ip in uban_list:
        json_map["uban"][str(ip)] = {
            "reason": ""
        }
    print(json_map)

    return json.dumps(json_map)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b","--ban",nargs="+",type=str,
                        help="ban ip's")
    parser.add_argument("-u", "--uban", nargs="+", type=str,
                        help="unban ip's")
    args = parser.parse_args()
    
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

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(socket_path)
    
    req = """action
{
  "ban": {
    "1.2.3.4": {
      "remark": "Cloudflare's web",
      "reason": "bot"
    },
    "8.8.8.8": {
      "remark": "",
      "reason": ""
    }
  },
  "uban": {
    "1.4.4.6": {
      "reason": "Misstake"
    },
    "1.0.0.1": {
      "reason": "DNS"
    }
  }
}
""" 
    req = request
    client.sendall(req.encode())
    client.shutdown(socket.SHUT_WR)
    print(client.recv(4096).decode())
    
