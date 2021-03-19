import subprocess

from setuptools import setup

try:
    ret = subprocess.check_output(
        "git describe --tags --abbrev=0",
        shell=True,
    )
    version = ret.decode("utf-8").strip()
except Exception:
    version = "main"

with open("README.md", "r", encoding="utf-8") as readme:
    long_description = readme.read()

setup(
    name="qballparser",
    version="0.1",
    description="NOMAD qball parser",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["nomad-lab"],
    packages=["qballparser"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
    ],
)
