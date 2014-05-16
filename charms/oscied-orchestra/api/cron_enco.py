from __future__ import absolute_import, division, print_function, unicode_literals

import logging, sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from os.path import abspath, dirname, join
from pytoolbox.encoding import configure_unicode
from pytoolbox.logging import setup_logging
from oscied_lib.api import ABOUT, get_test_api_core, OrchestraAPICore
from oscied_lib.config import OrchestraLocalConfig
from oscied_lib.config_test import ORCHESTRA_CONFIG_TEST
from oscied_lib.constants import LOCAL_CONFIG_FILENAME

from time import time

CONFIG_FILENAME = join(abspath(dirname(__file__)), LOCAL_CONFIG_FILENAME)

if __name__ == '__main__':
    local_config = OrchestraLocalConfig.read(CONFIG_FILENAME, inspect_constructor=False)
    api_core = OrchestraAPICore(local_config)

    user_id = "12f67500-aa53-4bc8-89e8-2e3da74c14e7" # David Fischer
    media_in_id = "cdd90479-f8aa-46dd-ba89-de2b1b5488fa" # bus_cif.webm
    profile_id = "3e051f17-3d56-4958-bc50-963ed502174e" # Force 720p
    title = 'cronjob_%s' % int(time())
    out_filename = title + ".webm"
    metadata = { 'title': title }
    send_email = 'false'
    queue = 'transform'

    orchestra.launch_transform_task(user_id, media_in_id, profile_id,
            out_filename, metadata, send_email, queue, u'/transform/callback')
