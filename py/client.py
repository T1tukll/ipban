#!/usr/bin/env python

import ipaddress
import os
import signal
import socket
import json
from collections.abc import Iterable

if __name__ == "__main__":
    socket_path = "/run/ipban/ipban.sock"

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(socket_path)
    
    client.sendall(b"""action
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
    "1.3.3.7": {
      "reason": "Misstake"
    },
    "1.0.0.1": {
      "reason": "DNS"
    }
  }
}
""")
    client.shutdown(socket.SHUT_WR)
    print(client.recv(4096).decode())
