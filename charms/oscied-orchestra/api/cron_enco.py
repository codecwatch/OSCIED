from __future__ import absolute_import, division, print_function, unicode_literals

import logging, sys, tempfile
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from os.path import abspath, dirname, join
from subprocess import check_output
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
    orchestra = OrchestraAPICore(local_config)

    user_id = "12f67500-aa53-4bc8-89e8-2e3da74c14e7" # David Fischer
    media_in_id = "cdd90479-f8aa-46dd-ba89-de2b1b5488fa" # bus_cif.webm
    send_email = 'false'
    queue = 'transform'

    profiles = orchestra.get_transform_profiles({'encoder_name': 'from_git'})
    for profile in profiles:

        profile_id = profile._id
        input_bitrates = [100,200,400,800,1600]

        if profile.title == "libvpx-vp8 git":
            extension = ".webm"
            git_url = "https://chromium.googlesource.com/webm/libvpx"
            build_cmds = "./configure --disable-vp9 --disable-unit-tests && make"
        elif profile.title == "x264 git":
            extension = ".mp4"
            git_url = "git://git.videolan.org/x264.git"
            build_cmds = "./configure && make"
        else:
            print(u'Unknown profile: "{0}"'.format(profile.title))
            continue


        tmpdir = tempfile.mkdtemp()
        # Use the same git commit for every file and every bitrate we encode for
        git_commit = check_output('git clone --quiet --depth=1 "{0}" "{1}" && cd "{1}" && git rev-parse HEAD && cd .. && rm -rf "{1}"'
                                  .format(git_url, tmpdir), shell=True).rstrip()

        for input_bitrate in input_bitrates:
            title = 'cronjob_%s_%s_%d' % (int(time()), profile.title, input_bitrate)
            out_filename = title + extension
            metadata = { 'title': title, 'git_url': git_url, 'git_commit': git_commit,
                         'build_cmds': build_cmds, 'input_bitrate': input_bitrate }
            print(metadata)
            orchestra.launch_transform_task(user_id, media_in_id, profile_id,
                    out_filename, metadata, send_email, queue,
                    u'/transform/callback')
