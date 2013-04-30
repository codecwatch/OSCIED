#!/usr/bin/env bash

#**************************************************************************************************#
#              OPEN-SOURCE CLOUD INFRASTRUCTURE FOR ENCODING AND DISTRIBUTION : WEB UI
#
#  Authors   : David Fischer
#  Contact   : david.fischer.ch@gmail.com / david.fischer@hesge.ch
#  Project   : OSCIED (OS Cloud Infrastructure for Encoding and Distribution)
#  Copyright : 2012 OSCIED Team. All rights reserved.
#**************************************************************************************************#
#
# This file is part of EBU/UER OSCIED Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this project.
# If not, see <http://www.gnu.org/licenses/>
#
# Retrieved from:
#   svn co https://claire-et-david.dyndns.org/prog/OSCIED

set -o nounset # will exit if an unitialized variable is used

# Constants ========================================================================================

ECHO='juju-log' # Used by logicielsUbuntuUtils

# Charms paths
BASE_PATH=$(pwd)

# Charms files
WEBUI_DB_FILE="$BASE_PATH/webui-db.sql"
SITE_TEMPL_FILE="$BASE_PATH/000-default"

# Shared storage paths
STORAGE_ROOT_PATH='/mnt/storage'
STORAGE_TEMP_PATH="$STORAGE_ROOT_PATH/tmp"
STORAGE_MEDIAS_PATH="$STORAGE_ROOT_PATH/medias"
STORAGE_UPLOADS_PATH="$STORAGE_ROOT_PATH/uploads"

# MySQL configuration files & paths
MYSQL_CONFIG_FILE='/etc/mysql/my.cnf'
MYSQL_TEMP_PATH='/var/lib/mysql/tmp'

# Web user interface paths
WWW_ROOT_PATH='/var/www'
WWW_MEDIAS_PATH="$WWW_ROOT_PATH/medias"
WWW_UPLOADS_PATH="$WWW_ROOT_PATH/uploads"

# Web user interface configuration files
SITES_ENABLED_PATH='/etc/apache2/sites-enabled'
GENERAL_CONFIG_FILE="$WWW_ROOT_PATH/application/config/config.php"
DATABASE_CONFIG_FILE="$WWW_ROOT_PATH/application/config/database.php"
HTACCESS_FILE="$WWW_ROOT_PATH/.htaccess"
ORCHESTRA_FLAG="$WWW_ROOT_PATH/orchestra_relation_ok"

# Configuration ====================================================================================

if [ "$(config-get verbose)" = 'true' ] ; then
  VERBOSE=0     # true
  set -o xtrace # for verbose logging to juju debug-log
else
  VERBOSE=1 # false
fi

PROXY_IPS=$(cat proxy_ips 2>/dev/null)
MAX_UPLOAD_SIZE=$(config-get max_upload_size)
MAX_EXECUTION_TIME=$(config-get max_execution_time)
MAX_INPUT_TIME=$(config-get max_input_time)

API_URL=$(config-get api_url)

STORAGE_IP=$(config-get storage_ip)
STORAGE_NAT_IP=$(config-get storage_nat_ip)
STORAGE_FSTYPE=$(config-get storage_fstype)
STORAGE_MOUNTPOINT=$(config-get storage_mountpoint)
STORAGE_OPTIONS=$(config-get storage_options)

MYSQL_MY_PASS=$(config-get mysql_my_password)
MYSQL_ROOT_PASS=$(config-get mysql_root_password)
MYSQL_USER_PASS=$(config-get mysql_user_password)

# Utilities ========================================================================================

api_config_is_enabled()
{
  [ "$API_URL" ]
}

api_hook_bypass()
{
  if api_config_is_enabled; then
    xecho 'Orchestrator is set in config, api relation is disabled' 1
  fi
}

api_register()
{
  # Overrides api parameters with charm configuration
  if api_config_is_enabled; then # if api options are set
    api_url=$API_URL
  # Or uses api parameters from charm api relation
  elif [ $# -eq 1 ]; then # if function parameters are set
    api_url=$1
  elif [ $# -eq 0 ]; then
    return
  else
    xecho "Usage: $(basename $0).api_register api_url"
  fi

  pecho 'Configure Web UI : Register the Orchestrator'
  setSettingPHP $GENERAL_CONFIG_FILE 'config' 'orchestra_api_url' "$api_url" || xecho 'Config'
  touch "$ORCHESTRA_FLAG" || xecho 'Unable to create flag'
}

api_unregister()
{
  pecho 'Configure Web UI : Unregister the Orchestrator'
  setSettingPHP $GENERAL_CONFIG_FILE 'config' 'orchestra_api_url' '' || xecho 'Config'
  rm -f "$ORCHESTRA_FLAG" 2>/dev/null
}

update_proxies()
{
  if [ $# -ne 2 ]; then
    xecho "Usage: $(basename $0).update_proxies action ip"
  fi
  action=$1
  ip=$2

  PROXY_IPS=$(cat proxy_ips 2>/dev/null)
  case "$action" in
  'add' )
    if ! echo $PROXY_IPS | grep -q "$ip"; then
      [ "$PROXY_IPS" ] && PROXY_IPS="$PROXY_IPS,"
      PROXY_IPS="$PROXY_IPS$ip"
      echo $PROXY_IPS > proxy_ips
      setSettingPHP $GENERAL_CONFIG_FILE 'config' 'proxy_ips' "$PROXY_IPS" || return $false
    fi ;;
  'remove' )
    if echo $PROXY_IPS | grep -q "$ip"; then
      sed -i "s<$ip,<<g;s<,$ip<<g;s<$ip<<g" proxy_ips
      PROXY_IPS=$(cat proxy_ips)
      setSettingPHP $GENERAL_CONFIG_FILE 'config' 'proxy_ips' "$PROXY_IPS" || return $false
    fi ;;
  'cleanup' )
    if "$PROXY_IPS"; then
      PROXY_IPS=''
      echo '' > proxy_ips
      setSettingPHP $GENERAL_CONFIG_FILE 'config' 'proxy_ips' "$PROXY_IPS" || return $false
    fi ;;
  * ) xecho "Unknown action : $action" ;;
  esac

  return $true
}

storage_config_is_enabled()
{
  [ "$STORAGE_IP" -a "$STORAGE_FSTYPE" -a "$STORAGE_MOUNTPOINT" ]
}

storage_is_mounted()
{
  mount | grep -q "$STORAGE_ROOT_PATH"
}

storage_remount()
{
  # Overrides storage parameters with charm configuration
  if storage_config_is_enabled; then # if storage options are set
    ip=$STORAGE_IP
    nat_ip=$STORAGE_NAT_IP
    fstype=$STORAGE_FSTYPE
    mountpoint=$STORAGE_MOUNTPOINT
    options=$STORAGE_OPTIONS
  # Or uses storage parameters from charm storage relation
  elif [ $# -eq 4 ]; then # if function parameters are set
    ip=$1
    nat_ip=''
    fstype=$2
    mountpoint=$3
    options=$4
  elif [ $# -eq 0 ]; then
    return
  else
    xecho "Usage: $(basename $0).storage_remount ip fstype mountpoint options"
  fi

  if [ "$nat_ip" ]; then
    pecho "Update hosts file to map storage internal address $ip to $nat_ip"
    if grep -q "$ip" /etc/hosts; then
      sed -i "s<$nat_ip .*<$nat_ip $ip<" /etc/hosts
    else
      echo "$nat_ip $ip" >> /etc/hosts
    fi
  else
    nat_ip=$ip
  fi

  storage_umount

  r=$STORAGE_ROOT_PATH
  pecho "Mount shared storage [$nat_ip] $ip:$mountpoint type $fstype options '$options' -> $r"
  if [ ! -d "$STORAGE_ROOT_PATH" ]; then
    mkdir "$STORAGE_ROOT_PATH" || xecho "Unable to create shared storage path $STORAGE_ROOT_PATH" 1
  fi

  # FIXME try 5 times, a better way to handle failure
  for i in $(seq 1 5)
  do
    if storage_is_mounted; then
      break
    else
      if [ "$options" ]
      then mount -t "$fstype" -o "$options" "$nat_ip:$mountpoint" "$STORAGE_ROOT_PATH"
      else mount -t "$fstype"               "$nat_ip:$mountpoint" "$STORAGE_ROOT_PATH"
      fi
    fi
    sleep 5
  done

  if storage_is_mounted; then
    storage_migrate_path 'medias'  "$STORAGE_MEDIAS_PATH"  "$WWW_MEDIAS_PATH"  'root'     755 644
    storage_migrate_path 'uploads' "$STORAGE_UPLOADS_PATH" "$WWW_UPLOADS_PATH" 'www-data' 755 644
    # FIXME update /etc/fstab (?)
    pecho 'Configure Web UI : Register shared storage'
    # FIXME this is a little bit cheating with paths ;-)
    storage_uri="$fstype://$ip/$mountpoint"
    uploads_uri="$storage_uri/uploads/"
    medias_uri="$storage_uri/medias/"
    setSettingPHP $GENERAL_CONFIG_FILE 'config' 'uploads_uri' "$uploads_uri" || xecho 'Config' 2
    setSettingPHP $GENERAL_CONFIG_FILE 'config' 'medias_uri'  "$medias_uri"  || xecho 'Config' 3
  else
    xecho 'Unable to mount shared storage' 4
  fi
}

storage_umount()
{
  pecho 'Configure Web UI : Unregister shared storage'
  setSettingPHP $GENERAL_CONFIG_FILE 'config' 'uploads_uri' '' || xecho 'Config' 1
  setSettingPHP $GENERAL_CONFIG_FILE 'config' 'medias_uri'  '' || xecho 'Config' 2

  if storage_is_mounted; then
    # FIXME update /etc/fstab (?)
    pecho 'Unmount shared storage (is actually mounted)'
    umount "$STORAGE_ROOT_PATH" || xecho 'Unable to unmount shared storage' 3
  else
    recho 'Shared storage already unmounted'
  fi
}

storage_hook_bypass()
{
  if storage_config_is_enabled; then
    xecho 'Shared storage is set in config, storage relation is disabled' 1
  fi
}

# Migrate a local Web UI path to shared storage only if necessary ----------------------------------
storage_migrate_path()
{
  if [ $# -ne 6 ]; then
    xecho "Usage: $(basename $0).storage_migrate_path name storage local owner dmod fmod"
  fi

  name=$1
  storage=$2
  local=$3
  owner=$4
  dmod=$5
  fmod=$6

  if [ ! -d "$storage" ]; then
    pecho "Create $name path in storage"
    mkdir -p "$storage" || xecho "Unable to create $name path" 1
  else
    recho "Storage $name path already created"
  fi

  if [ -d "$local" ]; then
    mecho "Migrating files from Web UI $name path to $name path in storage ..."
    rsync -a "$local/" "$storage/" || xecho "Unable to migrate $name files" 2
    rm -rf "$local"
  fi

  if [ ! -h "$local" ]; then
    pecho "Link Web UI $name path to $name path in storage"
    ln -s "$storage" "$local" || xecho "Unable to create $name link" 3
  fi

  pecho "Ensure POSIX rights (owner=$owner:$owner mod=(d=$dmod,f=$fmod)) of $name path in storage"
  chown "$owner:$owner" "$storage" -R || xecho "Unable to chown $storage" 4
  find "$storage" -type d -exec chmod "$dmod" "$storage" \;
  find "$storage" -type f -exec chmod "$fmod" "$storage" \;
}

# HOOKS : Charm Setup ==============================================================================

hook_install()
{
  techo 'Web UI - install'

  # Fix memtest86+ : https://bugs.launchpad.net/ubuntu/+source/grub2/+bug/1069856
  #eval $purge grub-pc grub-common
  #eval $install grub-common grub-pc

  eval $update
  eval $upgrade

  pecho 'Install and configure Network Time Protocol'
  eval $install ntp || xecho 'Unable to install ntp' 1
  eval $service ntp restart || xecho 'Unable to restart ntp service' 2

  techo 'Install and configure MySQL'
  sql='mysql-server mysql-server' # Tip : http://ubuntuforums.org/showthread.php?t=981801
  echo "$sql/root_password select $MYSQL_ROOT_PASS"       | debconf-set-selections
  echo "$sql/root_password_again select $MYSQL_ROOT_PASS" | debconf-set-selections
  mkdir /etc/mysql 2>/dev/null
  eval $install mysql-server glusterfs-client nfs-common || xecho 'Unable to install packages' 3

  # Now MySQL will listen to incoming request of any source
  #sed -i 's/127.0.0.1/0.0.0.0/g' /etc/mysql/my.cnf

  root=$MYSQL_ROOT_PASS

  # Fix ticket #57 : Keystone + MySQL = problems
  mysql -uroot -p"$root" -e "DROP USER ''@'localhost'; DROP USER ''@'$(hostname)';"
  mysql -uroot -p"$root" -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;"
  mysql -uroot -p"$root" -e "SET PASSWORD FOR 'root'@'%' = PASSWORD('$MYSQL_ROOT_PASS');"

  service mysql restart || xecho 'Unable to restart mysql' 4

  pecho 'Import Web User Interface database'
  mysql -u root -p"$MYSQL_ROOT_PASS" < "$WEBUI_DB_FILE" || xecho 'Unable to import database' 5

  pecho 'Create Web User Interface user'
  user='webui'
  pass="$MYSQL_USER_PASS"
  mysql -u root -p"$MYSQL_ROOT_PASS" \
    -e "GRANT ALL ON webui.* TO '$user'@'%' IDENTIFIED BY '$pass';" || \
    xecho 'Unable to create user' 6

  pecho 'Install and configure Apache2 + PHP'
  my='phpmyadmin phpmyadmin' # Tip : http://gercogandia.blogspot.ch/2012/11/automatic-unattended-install-of.html
  echo "$my/app-password password $MYSQL_MY_PASS"         | debconf-set-selections
  echo "$my/app-password-confirm password $MYSQL_MY_PASS" | debconf-set-selections
  echo "$my/mysql/admin-pass password $MYSQL_ROOT_PASS"   | debconf-set-selections
  echo "$my/mysql/app-pass password $MYSQL_ROOT_PASS"     | debconf-set-selections
  echo "$my/reconfigure-webserver multiselect apache2"    | debconf-set-selections
  eval $install apache2 php5 php5-cli php5-curl php5-gd php5-mysql libapache2-mod-auth-mysql \
    phpmyadmin || xecho 'Unable to install packages' 7

  a2enmod rewrite

  pecho 'Copy and configure Web User Interface'
  cp -f "$SITE_TEMPL_FILE" "$SITES_ENABLED_PATH"
  rsync -rtvh --progress --delete --exclude=.svn "www/" "/var/www/"
  key=$(randpass 32 $false $false $false)
  c='Config'
  setSettingBASH $MYSQL_CONFIG_FILE    $true 'tmpdir' "$MYSQL_TEMP_PATH"            || xecho $c 8
  setSettingPHP  $GENERAL_CONFIG_FILE  'config' 'encryption_key'  "$key"            || xecho $c 9
  setSettingPHP  $GENERAL_CONFIG_FILE  'config' 'proxy_ips'       "$PROXY_IPS"      || xecho $c 10
  setSettingPHP  $DATABASE_CONFIG_FILE 'db' 'default' 'hostname' 'localhost'        || xecho $c 11
  setSettingPHP  $DATABASE_CONFIG_FILE 'db' 'default' 'username' 'webui'            || xecho $c 12
  setSettingPHP  $DATABASE_CONFIG_FILE 'db' 'default' 'password' "$MYSQL_USER_PASS" || xecho $c 13
  setSettingPHP  $DATABASE_CONFIG_FILE 'db' 'default' 'database' 'webui'            || xecho $c 14
  mkdir -p                "$MYSQL_TEMP_PATH"
  chown mysql:mysql       "$MYSQL_TEMP_PATH"
  chown www-data:www-data "$WWW_ROOT_PATH" -R

  # config php, mettre short opentags à "on"
  # lire les logs, problème MY_ my_ nom fichier

  pecho 'Expose Apache 2 service'
  open-port 80/tcp

  # FIXME this call is not necessary, but config-changed create an infinite loop, so WE call it
  hook_config_changed
}

hook_uninstall()
{
  techo 'Web UI - uninstall'

  hook_stop
  eval $purge apache2 php5 php5-cli php5-gd php5-mysql libapache2-mod-auth-mysql phpmyadmin \
    apache2.2-common mysql-client-5.5 mysql-client-core-5.5 mysql-common mysql-server \
    mysql-server-5.1 mysql-server-5.5 mysql-server-core-5.5 glusterfs-client nfs-common
  eval $autoremove
  rm -rf /etc/apache2/ /var/www/ /var/log/apache2/ /etc/mysql/ /var/lib/mysql/ /var/log/mysql/
  mkdir /var/www/
}

hook_config_changed()
{
  techo 'Web UI - config changed'

  hook_stop
  pecho 'Configure Web UI : Set limits (upload size, execution time, ...)'
  c='Config'
  upload='upload_max_filesize'
  execution='max_execution_time'
  setSettingPHP $GENERAL_CONFIG_FILE 'config' 'max_upload_size' "$MAX_UPLOAD_SIZE"    || xecho $c 1
  setSettingPHP $GENERAL_CONFIG_FILE 'config' 'uploads_path'    "$WWW_UPLOADS_PATH/"  || xecho $c 2
  setSettingPHP $GENERAL_CONFIG_FILE 'config' 'medias_path'     "$WWW_MEDIAS_PATH/"   || xecho $c 3
  setSettingHTA $HTACCESS_FILE $true "php_value $upload"        "$MAX_UPLOAD_SIZE"    || xecho $c 4
  setSettingHTA $HTACCESS_FILE $true 'php_value post_max_size'  "$MAX_UPLOAD_SIZE"    || xecho $c 5
  setSettingHTA $HTACCESS_FILE $true "php_value $execution"     "$MAX_EXECUTION_TIME" || xecho $c 6
  setSettingHTA $HTACCESS_FILE $true 'php_value max_input_time' "$MAX_INPUT_TIME"     || xecho $c 7
  storage_remount
  api_register
  hook_start
  # FIXME infinite loop is used as config-changed hook !
}

# HOOKS : Charm Service ============================================================================

hook_start()
{
  techo 'Web UI - start'

  if ! storage_is_mounted; then
    recho 'WARNING Do not start Web UI : No shared storage'
  elif [ ! -f "$ORCHESTRA_FLAG" ]; then
    recho 'WARNING Do not start Web UI : No Orchestrator API'
  else
    if ! service mysql status | grep -q 'running'; then
      service mysql start || xecho 'Unable to start MySQL' 1
    fi
    service apache2 start || xecho 'Unable to start Apache 2' 2
  fi
}

hook_stop()
{
  techo 'Web UI - stop'

  service apache2 stop || xecho 'Unable to stop Apache 2' 1
  if service mysql status | grep -q 'running'; then
    service mysql stop || xecho 'Unable to stop MySQL' 2
  fi
}

# HOOKS : Requires API =========================================================================

hook_api_relation_joined()
{
  techo 'Web UI - api relation joined'
  api_hook_bypass
}

hook_api_relation_changed()
{
  techo 'Web UI - api relation changed'
  api_hook_bypass

  # Get configuration from the relation
  ip=$(relation-get private-address)
  api_url=$(relation-get api_url)

  mecho "Orchestrator IP is $ip, API URL is $api_url"
  if [ ! "$ip" -o ! "$api_url" ]; then
    recho 'Waiting for complete setup'
    exit 0
  fi

  hook_stop
  api_register "$api_url"
  hook_start
}

hook_api_relation_broken()
{
  techo 'Web UI - api relation broken'
  api_hook_bypass

  hook_stop
  api_unregister
}

# HOOKS : Requires Storage =========================================================================

hook_storage_relation_joined()
{
  techo 'Web UI - storage relation joined'
  storage_hook_bypass
}

hook_storage_relation_changed()
{
  techo 'Web UI - storage relation changed'
  storage_hook_bypass

  # Get configuration from the relation
  ip=$(relation-get private-address)
  fstype=$(relation-get fstype)
  mountpoint=$(relation-get mountpoint)
  options=$(relation-get options)

  mecho "Storage IP is $ip, fstype: $fstype, mountpoint: $mountpoint, options: $options"
  if [ ! "$ip" -o ! "$fstype" -o ! "$mountpoint" ]; then
    recho 'Waiting for complete setup'
    exit 0
  fi

  hook_stop
  storage_remount "$ip" "$fstype" "$mountpoint" "$options"
  hook_start
}

hook_storage_relation_broken()
{
  techo 'Web UI - storage relation broken'
  storage_hook_bypass

  hook_stop
  storage_umount
}

# HOOKS : Provides Website =========================================================================

hook_website_relation_joined()
{
  techo 'Web UI - website relation joined'

  # Send port & hostname
  relation-set port=80 hostname=$(hostname -f)
}

hook_website_relation_changed()
{
  techo 'Web UI - website relation changed'

  # Get configuration from the relation
  proxy_ip=$(relation-get private-address)

  mecho "Proxy IP is $proxy_ip"
  if [ ! "$proxy_ip" ]; then
    recho 'Waiting for complete setup'
    exit 0
  fi

  hook_stop
  pecho "Configure Web UI : Add $proxy_ip to allowed proxy IPs"
  update_proxies add "$proxy_ip" || xecho 'Unable to add proxy'
  hook_start
}

hook_website_relation_departed()
{
  techo 'Web UI - website relation departed'

  # Get configuration from the relation
  proxy_ip=$(relation-get private-address)

  mecho "Proxy IP is $proxy_ip"
  if [ ! "$proxy_ip" ]; then
    recho 'Waiting for complete setup'
    exit 0
  fi

  hook_stop
  pecho "Configure Web UI : Remove $proxy_ip from allowed proxy IPs"
  update_proxies remove "$proxy_ip" || xecho 'Unable to remove proxy'
  hook_start
}

hook_website_relation_broken()
{
  techo 'Web UI - website relation broken'

  # Get configuration from the relation
  proxy_ip=$(relation-get private-address)

  mecho "Proxy IP is $proxy_ip"
  if [ ! "$proxy_ip" ]; then
    recho 'Waiting for complete setup'
    exit 0
  fi

  hook_stop
  pecho "Configure Web UI : Remove $proxy_ip from allowed proxy IPs"
  update_proxies remove "$proxy_ip" || xecho 'Unable to remove proxy'
  # FIXME does relation broken means that no more proxies are linked to us ? if yes :
  #pecho 'Configure Web UI : Cleanup allowed proxy IPs'
  #update_proxies cleanup || xecho 'Unable to cleanup proxies'
  hook_start
}
# START OF LOGICIELS UBUNTU UTILS (licencing : LogicielsUbuntu project's licence)
# Retrieved from:
#   svn co https://claire-et-david.dyndns.org/prog/LogicielsUbuntu/public

# Prevent importing N times the following (like C++ .h : #ifndef ... #endif)
if ! logicielsUbuntuUtilsImported 2>/dev/null; then

# Colored echoes and yes/no question ===============================================================

true=0
false=1
true_auto=2
false_auto=3

if [ -t 0 ]; then
  TXT_BLD=$(tput bold)
  TXT_BLK=$(tput setaf 0)
  TXT_RED=$(tput setaf 1)
  TXT_GREEN=$(tput setaf 2)
  TXT_YLW=$(tput setaf 3)
  TXT_BLUE=$(tput setaf 4)
  TXT_PURPLE=$(tput setaf 5)
  TXT_CYAN=$(tput setaf 6)
  TXT_WHITE=$(tput setaf 7)
  TXT_RESET=$(tput sgr0)

  TECHO_COLOR=$TXT_GREEN
  PECHO_COLOR=$TXT_BLUE
  MECHO_COLOR=$TXT_YLW
  CECHO_COLOR=$TXT_YLW
  RECHO_COLOR=$TXT_PURPLE
  QECHO_COLOR=$TXT_CYAN
  XECHO_COLOR=$TXT_RED
else
  TXT_BLD=''
  TXT_BLK=''
  TXT_RED=''
  TXT_GREEN=''
  TXT_YLW=''
  TXT_BLUE=''
  TXT_PURPLE=''
  TXT_CYAN=''
  TXT_WHITE=''
  TXT_RESET=''

  TECHO_COLOR='[TITLE] '
  PECHO_COLOR='[PARAGRAPH] '
  MECHO_COLOR='[MESSAGE] '
  CECHO_COLOR='[CODE] '
  RECHO_COLOR='[REMARK] '
  QECHO_COLOR='[QUESTION] '
  XECHO_COLOR=''
fi

if echo "\n" | grep -q 'n'
then e_='-e'
else e_=''
fi

# By default output utility is the well known echo, but you can use juju-log with ECHO='juju-log'
echo=${ECHO:=echo}

# Disable echo extra parameter if output utility is not echo
[ "$echo" != 'echo' ] && e_=''

#if [ -z $DISPLAY ]
#then DIALOG=dialog
#else DIALOG=Xdialog
#fi
DIALOG=dialog

techo() { $echo $e_ "$TECHO_COLOR$TXT_BLD$1$TXT_RESET"; } # script title
pecho() { $echo $e_ "$PECHO_COLOR$1$TXT_RESET";         } # text title
mecho() { $echo $e_ "$MECHO_COLOR$1$TXT_RESET";         } # message (text)
cecho() { $echo $e_ "$CECHO_COLOR> $1$TXT_RESET";       } # message (code)
recho() { $echo $e_ "$RECHO_COLOR$1 !$TXT_RESET";       } # message (remark)
qecho() { $echo $e_ "$QECHO_COLOR$1 ?$TXT_RESET";       } # message (question)
becho() { $echo $e_ "$TXT_RESET$1";                     } # message (reset)

xecho() # message (error)
{
  [ $# -gt 1 ] && code=$2 || code=1
  $echo $e_ "${XECHO_COLOR}[ERROR] $1 (code $code)$TXT_RESET" >&2
  pause
  exit $code
}

pause() # menu pause
{
  [ ! -t 0 ] && return # skip if non interactive
  $echo $e_ 'press any key to continue ...'
  read ok </dev/tty
}

readLine() # menu read
{
  qecho "$1"
  read CHOICE </dev/tty
}

# use sudo only if we're not root & if available
if [ "$(id -u)" != '0' -a "$(which sudo)" != '' ]
then udo='sudo'
else udo=''
fi

service="$udo service"
if ! which service > /dev/null; then
  service() # replace missing 'service' binary !
  {
    if [ $# -ne 2 ]; then
      xecho "Usage: $(basename $0).service name argument"
    fi
    $udo /etc/init.d/$1 $2
  }
fi

if which apt-get > /dev/null; then
  installPack="$udo dpkg -i"
  install="$udo apt-get -fyq --force-yes install"
  buildDep="$udo apt-get -fyq --force-yes build-dep"
  update="$udo apt-get -fyq --force-yes update"
  upgrade="$udo apt-get -fyq --force-yes upgrade"
  distupgrade="$udo apt-get -fyq --force-yes dist-upgrade"
  remove="$udo apt-get -fyq --force-yes remove"
  autoremove="$udo apt-get -fyq --force-yes autoremove"
  purge="$udo apt-get -fyq --force-yes purge"
  key="$udo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys"
  packages="dpkg --get-selections"
elif which ipkg > /dev/null; then
  installPack="$udo ipkg install"
  install="$udo ipkg install"
  buildDep="xecho 'buildDep not implemented' #"
  update="$udo ipkg update"
  upgrade="$udo ipkg upgrade"
  distupgrade="$udo ipkg upgrade"
  remove="$udo ipkg remove"
  autoremove="xecho 'autoremove not implemented' #"
  purge="$udo ipkg remove"
  key="xecho 'key not implemented'"
  packages="xecho 'packages not implemented'"
else
  xecho 'Unable to find apt-get nor ipkg in your system'
fi

#if ! pushd . 2>/dev/null; then
#  recho 'pushd/popd as internal functions'
#  dirLifo=''
#  pushd()
#  {
#    if [ $# -ne 1 ]; then
#      xecho "Usage: $(basename $0).pushd path"
#    fi
#    dirLifo="$(pwd):$dirLifo"
#    cd "$1"
#  }
#  popd()
#  {
#    dir=$(echo $dirLifo | cut -d ':' -f1)
#    dirLifo=$(echo $dirLifo | cut -d ':' -f2-)
#    if [ "$dir" ]; then
#      cd "$dir"
#    else
#      xecho 'Paths LIFO is empty !'
#    fi
#  }
#else
#  recho 'pushd/popd as shell built-in'
#  popd
#fi

# unit-testing of the implementation !
#pushdTest()
#{
#  pushdUnitFailed="pushd/popd unit test failed !"
#  here=$(pwd)
#  pushd /media && echo $dirLifo
#  if [ "$(pwd)" != '/media' ]; then xecho "$pushdUnitFailed 1/5"; fi
#  cd /home
#  pushd /bin && echo $dirLifo
#  if [ "$(pwd)" != '/bin' ]; then xecho "$pushdUnitFailed 2/5"; fi
#  popd && echo $dirLifo
#  if [ "$(pwd)" != '/home' ]; then xecho "$pushdUnitFailed 3/5 $(pwd)"; fi
#  popd && echo $dirLifo
#  if [ "$(pwd)" != "$here" ]; then xecho "$pushdUnitFailed 4/5"; fi
#}

# Asks user to confirm an action (with yes or no) --------------------------------------------------
#> 0 (true value for if [ ]) if yes, 1 if no and (defaultChoice) by default
#1 : default (0 = yes / 1 = no)
#2 : question (automatically appended with [Y/n] ? / [y/N] ?)
yesOrNo()
{
  if [ $# -ne 2 ]; then
    xecho "Usage : yesOrNo default question\n\tdefault : 0=yes or 1=no 2='force yes' 3='force no'"
  fi

  local default="$1"
  local question="$2"
  case $default in
  "$true"       ) qecho "$question [Y/n]";;
  "$false"      ) qecho "$question [y/N]";;
  "$true_auto"  ) REPLY=$true;  return $true ;;
  "$false_auto" ) REPLY=$false; return $true ;;
  * ) xecho "Invalid default value : $default";;
  esac

  while true; do
    read REPLY </dev/tty
    case "$REPLY" in
    '' ) REPLY=$default ;;
    'y' | 'Y' ) REPLY=$true  ;;
    'n' | 'N' ) REPLY=$false ;;
    * ) REPLY='' ;;
    esac
    if [ "$REPLY" ]; then break; fi
    default='' # cancel default value
    recho "Please answer y for yes or n for no"
  done
}

# Utilities ========================================================================================

threadsCount()
{
  grep -c ^processor /proc/cpuinfo
}

# Checkout a subversion repository locally ---------------------------------------------------------
# TODO
checkout()
{
  [ $# -ne 4 ] && return $false

  rm -rf $2 2>/dev/null
  svn checkout --username=$3 --password=$4 --non-interactive --trust-server-cert $1 $2
}

# Generate a random password -----------------------------------------------------------------------
# size      : number of characters; defaults to 32
# special   : include special characters
# lowercase : convert any characters to lower case
# uppercase : convert any characters to upper case
randpass()
{
  [ $# -ne 4 ] && echo ''

  [ $2 -eq $true ] && chars='[:graph:]' || chars='[:alnum:]'
  [ $3 -eq $true ] && lower='[:upper:]' || lower='[:lower:]'
  [ $4 -eq $true ] && upper='[:lower:]' || upper='[:upper:]'
  cat /dev/urandom | tr -cd "$chars" | head -c $1 | \
    tr '[:upper:]' "$lower" | tr '[:lower:]' "$upper"
}

# Add a repository if it isn't yet listed in sources.list ------------------------------------------
# repositoryName   : the name (eg : virtualbox) of the repo.
# repositoryDebUrl : the debian URL (http://...) of the repo.
# repositoryKind   : the kind (contrib, ...) of the repo.
addAptRepo()
{
  if [ $# -ne 3 ]; then
    xecho 'Usage : addAptRepo repositoryName repositoryDebUrl repositoryKind'
  fi

  local release="$(lsb_release -cs)"
  if [ ! -f "/etc/apt/sources.list.d/$1.list" ]; then
    $udo sh -c "echo 'deb $2 $release $3' >> '/etc/apt/sources.list.d/$1.list'"
  fi
}

# Add a 'ppa' repository trying to fix TODO --------------------------------------------------------
# repositoryPpa : the PPA (eg : ppa:rabbitvcs/ppa) of the repo.
# repositoryName : the PPA name without ppa:/... TODO
addAptPpaRepo()
{
  if [ $# -ne 2 ]; then
    xecho 'Usage : addAptPpaRepo repositoryPpa repositoryName'
  fi

  local repositoryPpa="$1"
  local repositoryName="$2"

  local ok=$false
  local here="$(pwd)"
  local last="$(lsb_release -cs)"
  cd /etc/apt/sources.list.d
  $udo rm -rf *$repositoryName*
  $udo apt-add-repository -y $repositoryPpa
  repositoryFile=$(ls | grep $repositoryName)
  if [ ! "$repositoryFile" ]; then
    xecho "Unable to find $repositoryName's repository file"
  fi
  mecho "Repository file : $repositoryFile"
  for actual in "$last" 'quantal' 'precise' 'oneiric' 'maverick' 'lucid'
  do
    $udo sh -c "sed -i -e 's:$last:$actual:g' $repositoryFile"
    mecho "Checking if the $repositoryName's repository does exist for $actual ..."
    if $update 2>&1 | grep -q $repositoryName; then
      mecho "Hum, the $repositoryName's repository does not exist for $actual"
      recho "Ok, trying the next one"
    else
      ok=$true
      break
    fi
    last=$actual
  done
  cd "$here"
  if [ $ok -eq $true ]
  then mecho "Using the $repositoryName's repository for $actual"
  else xecho 'Unable to find a suitable repository !'
  fi
}

# Add a GPG key to the system ----------------------------------------------------------------------
# gpgKeyUrl : the URL (deb http://....asc) of the GPG key
addGpgKey()
{
  if [ $# -ne 1 ]; then
    xecho 'Usage : addGpgKey gpgKeyUrl'
  fi

  wget -q "$1" -O- | $udo apt-key add -
}

# Check if a package is installed ------------------------------------------------------------------
# packageName : name of the package to check
isInstalled()
{
  if [ $# -ne 1 ]; then
    xecho 'Usage : isInstalled packageName'
  fi

  if $packages | grep $1 | grep -v -q 'deinstall'
  then return $true
  else return $false
  fi
}

# Install a package if it isn't yet installed ------------------------------------------------------
# packageName : name of the package to install
# binaryName  : name of the binary to find
autoInstall()
{
  if [ $# -ne 2 ]; then
    xecho 'Usage : autoInstall packageName binaryName'
  fi

  local packageName="$1"
  local binaryName="$2"

  # install the package if missing
  if which "$binaryName" > /dev/null; then
    recho "Binary $binaryName of package $packageName founded, nothing to do"
  else
    recho "Binary $binaryName of package $packageName missing, installing it"
    eval $install $packageName || xecho "Unable to install package $packageName !"
  fi
}

# Install a package if it isn't yet installed ------------------------------------------------------
# libName : name of the package to install (library)
autoInstallLib()
{
  if [ $# -ne 1 ]; then
    xecho 'Usage : autoInstallLib libName'
  fi

  # install the libs package if missing
  if dpkg --get-selections | grep "$1" | grep -q install; then
    recho "Library $1 founded, nothing to do"
  else
    recho "Library $1 missing, installing it"
    eval $install $1
  fi
}

# Install a package (with a setup method) if it isn't yet installed --------------------------------
# setupName  : name of the (setup) method to execute
# binaryName : name of the binary to find
autoInstallSetup()
{
  if [ $# -ne 2 ]; then
    xecho 'Usage : autoInstallSetup setupName binaryName'
  fi

  local setupName="$1"
  local binaryName="$2"

  # install the package if missing
  if which "$binaryName" > /dev/null; then
    recho "Binary $binaryName of setup $setupName founded, nothing to do"
  else
    recho "Binary $binaryName of setup $setupName missing, installing it"
    $setupName
  fi
}

# Extract a debian package -------------------------------------------------------------------------
debianDepack()
{
  if [ $# -ne 1 ]; then
    xecho "Usage: $(basename $0) debianFilename"
  fi

  local name=$(basename "$1" .deb)
  dpkg-deb -x "$1" "$name"
  mkdir "$name/DEBIAN"
  dpkg-deb -e "$1" "$name/DEBIAN"
}

# Create a debian package of a folder --------------------------------------------------------------
debianRepack()
{
  if [ $# -ne 1 ]; then
    xecho "Usage: $(basename $0) debianPath"
  fi

  dpkg-deb -b "$1"
}

checkDepend()
{
  if [ $# -ne 1 ]; then
    xecho 'Usage : checkDepend binaryName methodName'
  fi

  if ! which "$1" > /dev/null; then
    xecho "Dependency : $2 depends of $1, unable to find $1"
  fi
}

validateNumber()
{
  if [ $# -ne 1 ]; then
    xecho "Usage: $(basename $0).validateNumber input"
  fi
  [ "$1" -eq "$1" 2>/dev/null ]
}

# Get the Nth first digits of the IPv4 address of a network interface ------------------------------
#> The address, ex: 192.168.1.34 -> [3 digits] 192.168.1. [1 digit] 192.
# ethName : name of the network interface to get ...
# numberOfDigitsRequired : number of digits to return (1-4)
getInterfaceIPv4()
{
  if [ $# -ne 2 ]; then
    xecho 'Usage : getInterfaceIPv4 ethName numberOfDigitsRequired'
  fi

  local ethName="$1"
  local numberOfDigitsRequired="$2"

  # find the Nth first digits of the ip address of a certain network interface,
  # this method use regular expression to filter the output of ifconfig
  cmd=$(ifconfig $ethName)
  case "$numberOfDigitsRequired" in
  '1' ) REPLY=$(expr match "$cmd" '.*inet ad\+r:\([0-9]*\.\)[0-9]*\.[0-9]*\.[0-9]*');;
  '2' ) REPLY=$(expr match "$cmd" '.*inet ad\+r:\([0-9]*\.[0-9]*\.\)[0-9]*\.[0-9]*');;
  '3' ) REPLY=$(expr match "$cmd" '.*inet ad\+r:\([0-9]*\.[0-9]*\.[0-9]*\.\)[0-9]*');;
  '4' ) REPLY=$(expr match "$cmd" '.*inet ad\+r:\([0-9]*\.[0-9]*\.[0-9]*\.[0-9]*\)');;
  * ) xecho 'numberOfDigitsRequired must be between 1 and 4' ;;
  esac

  # FIXME : check du parsing !
}

# Get the name of the default network interface ----------------------------------------------------
getDefaultInterfaceName()
{
  local default="$(route | grep ^default)"
  REPLY=$(expr match "$default" '.* \(.*\)$')
  if [ ! "$REPLY" ]; then
    xecho '[BUG] Unable to detect default network interface'
  fi
}

validateIP()
{
  if [ $# -ne 1 ]; then
    xecho "Usage: $(basename $0).validateIP ip"
  fi
  [ $(echo $1 | sed -n "/^[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*$/p") ]
}

validateMAC()
{
  if [ $# -ne 1 ]; then
    xecho "Usage: $(basename $0).validateMAC mac"
  fi
  [ $(echo $1 | sed -n "/^\([0-9A-Za-z][0-9A-Za-z]:\)\{5\}[0-9A-Za-z][0-9A-Za-z]$/p") ]
}

# Set setting value of a 'JSON' configuration file -------------------------------------------------
# TODO parameters comment
setSettingJSON_STRING()
{
  if [ $# -ne 3 ]; then
    xecho "Usage: $(basename $0).setSettingJSON file name value"
  fi

  sed  -i "s<\"$2\" *: *\"[^\"]*\"<\"$2\": \"$3\"<g" "$1"
  grep -q "\"$2\": \"$3\"" "$1"
}

# Set setting value of a 'JSON' configuration file -------------------------------------------------
# TODO parameters comment
setSettingJSON_BOOLEAN()
{
  if [ $# -ne 3 ]; then
    xecho "Usage: $(basename $0).setSettingJSON file name value"
  fi

  [ $3 -eq $true ] && value='true' || value='false'
  sed  -i "s<\"$2\" *: *[a-zA-Z]*<\"$2\": $value<g" "$1"
  grep -q "\"$2\": $value" "$1"
}

# Set setting value of a 'BASH' configuration file -------------------------------------------------
# TODO parameters comment
setSettingBASH()
{
  if [ $# -ne 3 -a $# -ne 4 ]; then
    xecho "Usage: $(basename $0).setSettingBASH file enabled name [value]"
  fi

  local toggle=''
  if [ $2 -eq $false ]; then toggle='#'; fi
  if [ $# -eq 3 ]; then
    sed  -i "s<[# \t]*$3<$toggle$3<" "$1"
    grep -q "$toggle$3" "$1"
  elif [ $# -eq 4 ]; then
    sed  -i "s<[# \t]*$3[ \t]*=.*<$toggle$3=$4<" "$1"
    grep -q "$toggle$3=$4" "$1"
  fi
}

# Set setting value of a 'htaccess' file -----------------------------------------------------------
# TODO parameters comments
setSettingHTA()
{
  if [ $# -ne 3 -a $# -ne 4 ]; then
    xecho "Usage: $(basename $0).setSettingHTA file enabled name [value]"
  fi

  local toggle=''
  if [ $2 -eq $false ]; then toggle='#'; fi
  if [ $# -eq 3 ]; then
    sed  -i "s<[# \t]*$3<$toggle$3<" "$1"
    grep -q "$toggle$3" "$1"
  elif [ $# -eq 4 ]; then
    sed  -i "s<[# \t]*$3[ \t]*.*<$toggle$3 $4<" "$1"
    grep -q "$toggle$3 $4" "$1"
  fi
}

# Set setting value of a 'PHP' configuration file --------------------------------------------------
# TODO parameters comments
setSettingPHP()
{
  if   [ $# -eq 4 ]; then key="\$$2\['$3'\]";         value=$4
  elif [ $# -eq 5 ]; then key="\$$2\['$3'\]\['$4'\]"; value=$5
  else xecho "Usage: $(basename $0).setSettingPHP file variable (category) name value"
  fi

  sed  -i "s<$key = .*<$key = '$value';<" "$1"
  grep -q "$key = '$value';" "$1"
}

screenRunning()
{
  if [ $# -ne 1 ]; then
    xecho "Usage: $(basename $0).screenRunning name"
  fi
  screen -list | awk '{print $1}' | grep -q "$1"
}

screenLaunch()
{
  if [ $# -lt 2 ]; then
    xecho "Usage: $(basename $0).screenLaunch name command"
  fi
  screen -dmS "$@"
}

screenKill()
{
  if [ $# -ne 1 ]; then
    xecho "Usage: $(basename $0).screenKill name"
  fi
  screen -X -S "$1" kill
}

# http://freesoftware.zona-m.net/how-automatically-create-opendocument-invoices-without-openoffice

# Apply sed in a [Libre|Open] Office document ------------------------------------------------------
# oooSrcFilename : name of the source [Libre|Open] office file
# oooDstFilename : name of the destination [Libre|Open] office file
# paramsFilename : name of the params file (a couple of param value by line)
oooSed()
{
  if [ $# -ne 3 ]; then
    xecho 'Usage : oooSed oooSrcFilename oooDstFilename paramsFilename'
  fi

  local work_dir='/tmp/OOO_SED'
  local oooSrcFilename="$1"
  local oooDstFilename="$2"
  local paramsFilename="$3"

  mecho "Apply sed in a [Libre|Open] Office document"
  mecho "Source         : $oooSrcFilename"
  mecho "Destination    : $oooDstFilename"
  mecho "Sed parameters : $paramsFilename"

  rm -rf $work_dir
  mkdir  $work_dir
  # FIXME local filename instead of filename, + test behaviour !
  filename=$(basename $oooSrcFilename)
  filename=$(echo ${filename%.*})

  cp $oooSrcFilename $work_dir/my_template
  cp $paramsFilename $work_dir/my_data.sh

  # preparation
  cd     $work_dir
  mkdir  work
  mv     my_template work
  cd     work
  unzip  my_template > /dev/null
  rm     my_template

  # replace text strings
  local content="$(cat content.xml)"
  local styles="$(cat styles.xml)"

  # parse params list line by line to find
  #          param value
  while read param value
  do
    if [ "$read$param" ]; then
      echo "s#$param#$value#g"
      content=$(echo $content | sed "s#$param#$value#g")
      styles=$(echo $styles | sed "s#$param#$value#g")
    fi
  done < ../my_data.sh # redirect done before while loop

  rm -f content.xml
  echo "$content" > content.xml

  rm -f styles.xml
  echo "$styles" > styles.xml

  # zip everything, rename it as .od* file and clean up
  find . -type f -print0 | xargs -0 zip ../$filename > /dev/null
  cd ..
  mv ${filename}.zip $oooDstFilename
  cd ..
  rm -rf $work_dir
}

# http://dag.wieers.com/home-made/unoconv/

# Convert a [Libre|Open] office document to a PDF with unoconv -------------------------------------
# oooSrcFilename : name of the [Libre|Open] office document to convert
oooToPdf()
{
  if [ $# -ne 3 ]; then
    xecho 'Usage : oooToPdf oooSrcFilename'
  fi

  unoconv -v --format pdf $1
}

logicielsUbuntuUtilsImported()
{
  echo > /dev/null
}
fi

# END OF LOGICIELS UBUNTU UTILS
