#!/usr/bin/env bash

#**********************************************************************************************************************#
#              OPEN-SOURCE CLOUD INFRASTRUCTURE FOR ENCODING AND DISTRIBUTION : SCRIPTS
#
#  Project Manager : Bram Tullemans (tullemans@ebu.ch)
#  Main Developer  : David Fischer (david.fischer.ch@gmail.com)
#  Copyright       : Copyright (c) 2012-2013 EBU. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of EBU Technology & Innovation OSCIED Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/ebu/OSCIED

cd ../library || { echo '[ERROR] Unable to find directory ../library'; exit 1; }
sudo python2 setup.py test || { echo '[ERROR] Python 2 unit-test of oscied_lib failed'; exit 2; }
sudo python3 setup.py test || { echo '[ERROR] Python 3 unit-test of oscied_lib failed'; exit 3; }
version=$(cat setup.py | grep version= | cut -d'=' -f2 | sed "s:',*::g")
echo "Release version $version, press enter to continue ..."
read a
git push || { echo '[ERROR] Unable to push to GitHub'; exit 4; }
git tag "$version" && git push origin "$version" || { echo '[ERROR] Unable to add release tag'; exit 5; }
#sudo python setup.py register && sudo python setup.py sdist upload
