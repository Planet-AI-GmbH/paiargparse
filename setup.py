from setuptools import setup, find_packages
import os

this_dir = os.path.dirname(os.path.realpath(__file__))

# Parse version
main_ns = {}
with open(os.path.join(this_dir, "paiargparse", "version.py")) as f:
    exec(f.read(), main_ns)
    __version__ = main_ns["__version__"]

setup(
    name="paiargparse",
    version=__version__,
    packages=find_packages(exclude=["test/*", "examples/*"]),
    license="MIT",
    long_description=open(os.path.join(this_dir, "README.md")).read(),
    long_description_content_type="text/markdown",
    author="Planet AI GmbH",
    author_email="admin@planet-ai.de",
    url="https://github.com/Planet-AI-GmbH/paiargparse",
    download_url="https://github.com/Planet-AI-GmbH/paiargparse/archive/{}.tar.gz".format(__version__),
    python_requires=">=3.7",
    install_requires=open(os.path.join(this_dir, "requirements.txt")).read().split("\n"),
    keywords=["argument parser", "dataclass", "hierarchical"],
    data_files=[("", [os.path.join(this_dir, "requirements.txt")])],
)
