import argparse
import json
import logging
import sys

from nomad.datamodel import EntryArchive
from nomad.utils import configure_logging

from .parser import QBallParser


def parse(filename: str):
    archive = EntryArchive()
    QBallParser().run(filename, archive, logging)
    json.dump(archive.m_to_dict(), sys.stdout, indent=2)


def main():
    configure_logging(console_log_level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="file to parse")
    args = parser.parse_args()

    parse(args.filename)


if __name__ == "__main__":
    main()
