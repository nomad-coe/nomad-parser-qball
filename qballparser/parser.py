import bz2
import datetime
import gzip
import lzma

from nomad.datamodel import EntryArchive, EntryMetadata
from nomad.datamodel.dft import DFTMetadata
from nomad.datamodel.metainfo.public import section_run as Run
from nomad.datamodel.metainfo.public import section_system as System
from nomad.datamodel.metainfo.public import SingleConfigurationCalculation
from nomad.metainfo.metainfo import Quantity
from nomad.parsing import FairdiParser
from nomad.parsing.file_parser import Quantity, UnstructuredTextFileParser

import xml.etree.ElementTree as ElementTree

import numpy as np

def str_to_timestamp(s: str):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").timestamp()

def pos_to_unit(v: float) -> float:
    return v * 0.5291765064371143

def force_to_unit(v: float) -> float:
    return v * 8.248232521602514e-08

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
        metadata.mainfile = mainfile

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

        element_tree = ElementTree.fromstring(contents)

        #section system
        system = run.m_create(System)

        system.atom_labels = [
            atom.attrib["name"]
            for atom in element_tree.find("run").find("iteration").find("atomset").iter("atom")
        ]

        system.atom_positions = np.array(
            [
                [pos_to_unit(float(pos)) for pos in atom.find("position").text.split()]
                for atom in element_tree.find("run").find("iteration").find("atomset").iter("atom")
            ]
        )

        #section SingleConfigurationCalculation
        single_configuration_calculation = run.m_create(SingleConfigurationCalculation)
        single_configuration_calculation.atom_forces = np.array(
            [
                [force_to_unit(float(force)) for force in atom.find("force").text.split()]
                for atom in element_tree.find("run").find("iteration").find("atomset").iter("atom")
            ]
        )


        # import code
        # code.interact(local={**locals(), **globals()})

    def parse(self, mainfile: str, archive: EntryArchive, logger=None) -> None:
        self.run(mainfile, archive, logger)
