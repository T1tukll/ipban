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

# synapsys:
# abort_install "reason"
abort_install() {
  cout "err" "%F{red}Install aborted:%f\t$1"
  exit 1
}

if [[ ! $(id -g ipban) ]]; then
  sudo groupadd --system ipban
else
  abort_install "Group %Bipban%b already exists"
fi

if [[ ! $(id -u ipban) ]]; then
  sudo useradd \
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

db_dir="/var/lib/ipban"
if [[ ! -d $db_dir ]]; then
  sudo mkdir $db_dir
  sudo chmod 775 $db_dir
  sudo chown ipban:ipban $db_dir
else
  if ask "n" "directory $db_dir already exists. rewrite?"; then
    sudo rm -rf $db_dir

    sudo mkdir $db_dir
    sudo chmod 775 $db_dir
    sudo chown ipban:ipban $db_dir
  else
    abort_install "User decided not to overwrite \'$db_dir\'. Which is requred to store banned ip\'s"
  fi
fi

#TODO: create systemd service
