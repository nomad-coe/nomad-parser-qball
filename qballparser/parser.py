import bz2
import datetime
import gzip
import lzma

from nomad.datamodel import EntryArchive, EntryMetadata
from nomad.datamodel.dft import DFTMetadata
from nomad.datamodel.metainfo.public import section_run as Run
from nomad.metainfo.metainfo import Quantity
from nomad.parsing import FairdiParser
from nomad.parsing.file_parser import Quantity, UnstructuredTextFileParser


def str_to_timestamp(s: str):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").timestamp()


class QBallParser(FairdiParser):

    mainfile_parser = UnstructuredTextFileParser(
        quantities=[
            Quantity(
                "atoms",
                # r"species (\w+):",
                r"symbol_ = (\w+)",
                # r"read symbol (\w+)"
                repeats=True,
            ),
            Quantity(
                "start_time",
                r"<start_time>\s*(.*?)\s*</start_time>",
                repeats=False,
            ),
            Quantity(
                "end_time",
                r"<end_time>\s*(.*?)\s*</end_time>",
                repeats=False,
            ),
        ]
    )

    def __init__(self):
        super().__init__(
            name="parsers/qball",
            code_name="qball",
            mainfile_contents_re="qball",
            supported_compressions=["gz", "bz2", "xz"],
        )

    def run(self, mainfile: str, archive: EntryArchive, logger):

        open_file = open
        if mainfile.endswith(".gz"):
            open_file = gzip.open
        elif mainfile.endswith(".bz2"):
            open_file = bz2.open
        elif mainfile.endswith(".xz"):
            open_file = lzma.open

        with open_file(mainfile, "rt") as file:
            contents = file.read()

        self.mainfile_parser.mainfile = mainfile
        self.mainfile_parser.parse()

        run = archive.m_create(Run)
        metadata = archive.m_create(EntryMetadata)
        dft = metadata.m_create(DFTMetadata)

        metadata.domain = "dft"

        # basis set check
        if "plane waves" not in contents:
            print("Qball Error: Not a plane wave dft")
        dft.basis_set = "plane waves"
        dft.crystal_system = "cubic"
        dft.code_name = "qball"

        # get atoms

        metadata.atoms = self.mainfile_parser.get("atoms")

        run.program_name = "qball"
        run.time_run_date_start = str_to_timestamp(
            self.mainfile_parser.get("start_time")
        )
        run.time_run_date_end = str_to_timestamp(
            self.mainfile_parser.get("end_time")
        )
