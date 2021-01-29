# Copyright 2020 The tfaip authors. All Rights Reserved.
#
# This file is part of tfaip.
#
# tfaip is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# tfaip is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# tfaip. If not, see http://www.gnu.org/licenses/.
# ==============================================================================
from setuptools import setup, find_packages
import os
from paiargparse import __version__

this_dir = os.path.dirname(os.path.realpath(__file__))


setup(
    name='paiargparse',
    version=__version__,
    packages=find_packages(exclude=['test/*']),
    license='MIT',
    long_description=open(os.path.join(this_dir, "README.md")).read(),
    long_description_content_type="text/markdown",
    author="Planet AI GmbH",
    author_email="admin@planet-ai.de",
    url="https://github.com/Planet-AI-GmbH/paiargparse",
    download_url='https://github.com/Planet-AI-GmbH/paiargparse/archive/{}.tar.gz'.format(__version__),
    python_requires='>=3.7',
    install_requires=open(os.path.join(this_dir, "requirements.txt")).read().split('\n'),
    test_requires=open(os.path.join(this_dir, "test_requirements.txt")).read().split('\n'),
    keywords=['argument parser', 'dataclass', 'hierarchical'],
    data_files=[('', [os.path.join(this_dir, "requirements.txt")])],
)
