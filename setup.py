from setuptools import setup, find_packages
import os
from paiargparse import __version__

this_dir = os.path.dirname(os.path.realpath(__file__))


setup(
    name='paiargparse',
    version=__version__,
    packages=find_packages(exclude=['test/*', 'examples/*']),
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
