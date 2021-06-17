import os
import re

from av1an.project import Project
from av1an.chunk import Chunk
from av1an.commandtypes import MPCommands, CommandPair, Command
from .encoder import Encoder
from av1an.utils import list_index_of_regex
from av1an_pyo3 import compose_ffmpeg_pipe
from av1an_pyo3 import compose_1_pass as pass1


class Vpx(Encoder):
    def compose_1_pass(self, a: Project, c: Chunk, output: str) -> MPCommands:
        return [
            CommandPair(
                compose_ffmpeg_pipe(a.ffmpeg_pipe),
                pass1(a.encoder, a.video_params, output),
            )
        ]

    def compose_2_pass(self, a: Project, c: Chunk, output: str) -> MPCommands:
        return [
            CommandPair(
                compose_ffmpeg_pipe(a.ffmpeg_pipe),
                [
                    "vpxenc",
                    "--passes=2",
                    "--pass=1",
                    *a.video_params,
                    f"--fpf={c.fpf}",
                    "-o",
                    os.devnull,
                    "-",
                ],
            ),
            CommandPair(
                compose_ffmpeg_pipe(a.ffmpeg_pipe),
                [
                    "vpxenc",
                    "--passes=2",
                    "--pass=2",
                    *a.video_params,
                    f"--fpf={c.fpf}",
                    "-o",
                    output,
                    "-",
                ],
            ),
        ]

    def man_q(self, command: Command, q: int) -> Command:
        """Return command with new cq value

        :param command: old command
        :param q: new cq value
        :return: command with new cq value"""

        adjusted_command = command.copy()

        i = list_index_of_regex(adjusted_command, r"--cq-level=.+")
        adjusted_command[i] = f"--cq-level={q}"

        return adjusted_command

    def match_line(self, line: str):
        """Extract number of encoded frames from line.

        :param line: one line of text output from the encoder
        :return: match object from re.search matching the number of encoded frames"""

        if "fatal" in line.lower():
            print("\n\nERROR IN ENCODING PROCESS\n\n", line)
            sys.exit(1)
        if "Pass 2/2" in line or "Pass 1/1" in line:
            return re.search(r"frame.*?/([^ ]+?) ", line)
