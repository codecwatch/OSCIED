echo 'Install OSCIED Library'
apt-get -y install build-essential git-core python-dev python-pip >/dev/null
# The following pre-download some python packages with pip to avoid the strange
# "mock" module not found ..., like setup.py sometimes fail to find packages !
#pip install --upgrade argparse configobj celery flask hashlib ipaddr mock mongoengine mongomock \
#  passlib pymongo requests six || { echo 'Unable to install python packages' 1>&2; exit 1; }
cd pyutils && ./setup.py develop || { echo 'Unable to install pyutils module' 1>&2; exit 2; }
cd .. && ./setup.py develop || { echo 'Unable to install oscied_lib module' 1>&2; exit 3; }
