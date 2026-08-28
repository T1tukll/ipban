#!/bin/zsh

# synapsys:
# cout "output_type" "message"
# supported output types:
#   inf war err
cout() {
  local msg="$2"
  local lead="[=]"
  if [[ "$1" == "war" ]]; then
    lead="[?]"
  fi
  if [[ "$1" == "inf" ]]; then
    lead="[=]"
  fi
  if [[ "$1" == "err" ]]; then
    lead="[!]"
  fi
  print -P "$lead" "$msg"
}


# synapsys:
# ask "default_ans" "message"
# 
# if user answers YES ask returns 0
# if NO, returns 1
# 
# ex: ask "y" "overwrite?"
#   out: overwrite? [Y/n]: 
ask() {
  local def_ans="$1"
  local promt
  if [[ "$def_ans" == "y" ]]; then
    promt="[Y/n]"
  elif [[ "$def_ans" == "n" ]]; then
    promt="[y/N]"
  else
    cout "err" "ask() got \$default_ans as $1"
    exit 10
  fi

  local msg="$2"
  while [[ true ]]; do
    local ans=''
    read -r "ans?$msg $promt: "
    local ans="${ans:l}"

    if [[ "$def_ans" == "y" ]]; then
      if [[ -z "$ans" || "$ans" == "y" || "$ans" == "yes" ]]; then
        return 0
      elif [[ "$ans" == "n" || "$ans" == "no" ]]; then
        return 1
      fi
    
    elif [[ "$def_ans" == "n" ]]; then
      if [[ -z "$ans" || "$ans" == "n" || "$ans" == "no" ]]; then
        return 1
      elif [[ "$ans" == "y" || "$ans" == "YES" ]]; then
        return 0
      fi
    fi
  done
  
}

rm_if_present() {
  local object="$1"
  if [[ -a "$object" ]]; then
    rm -fr "$object"
  fi
}

# synapsys:
# abort_install "reason"
abort_install() {
  cout "err" "%F{red}Install aborted:%f\t$1"
  exit 1
}

#--------[main]---------

if [[ ${EUID} != 0 ]]; then
  abort_install "Root privilegies are required to run installation"
fi

if [[ ! $(id -g ipban) ]]; then
  groupadd --system ipban
else
  abort_install "Group %Bipban%b already exists"
fi

if [[ ! $(id -u ipban) ]]; then
  useradd \
    --system \
    --gid ipban \
    --no-create-home \
    --comment "ipban service" \
    --home-dir / \
    --shell /sbin/nologin \
    ipban
else
  abort_install "User %Bipban%b already exists"
fi

daemon_dir="/opt/ipban"
if [[ ! -d $daemon_dir ]]; then
  #creating directory for daemon
  mkdir $daemon_dir
  chmod u=rx,g=rx,o=- $daemon_dir
  chown ipban:ipban $daemon_dir
else
  if ask "n" "directory $daemon_dir already exists. overwrite?"; then
    rm -rf $daemon_dir
    mkdir $daemon_dir
    chmod u=rx,g=rx,o=- $daemon_dir
    chown ipban:ipban $daemon_dir
  else
    abort_install  "User decided not to overwrite \'$daemon_dir\'. Which is needed for daemon"
  fi 
  
  #copying daemon to it's dir
  cp ./py/daemon.py $daemon_dir/daemon.py
  chmod u=rx,g=rx,o=- $daemon_dir/daemon.py
  chown ipban:ipban $daemon_dir/daemon.py
fi

bin_client="/bin/ipban"
sbin_client="/sbin/ipban"
if [[ ! -f $bin_client ]]; then
  if ! ask "n" "$bin_client already exists. overwrite?"; then
    abort_install "Couldn't install ipban client."
  fi
fi
if [[ ! -f $sbin_client ]]; then
  if ! ask "n" "$sbin_client already exists. overwrite?"; then
    abort_install "Couldn't install ipban client."
  fi
fi

#client binary
cp ./py/client.py "$bin_client"
cp ./py/client.py "$sbin_client"

#systemd service
systemd_service="./systemd/ipban.service"
cp "$systemd_service" /etc/systemd/system
systemctl enable --now ipban.service
