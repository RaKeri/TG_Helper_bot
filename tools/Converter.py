import os
import subprocess
import random
import traceback


class Converter:
    @staticmethod
    async def ogg_to_mp3(file):
        output_file = str(random.randint(1, 10000000)) + '.mp3'
        pathdir = os.path.dirname(os.path.abspath(__file__)).split("\\")[:-1]
        pathdir = "\\".join(pathdir) + "\\"
        command = pathdir + 'bin/ffmpeg -i "'+pathdir + file + '" -vn -ar 44100 -ac 2 -ab 192k -f mp3 "' +pathdir+ output_file + '"'
        subprocess.run(command, shell=True)
        return pathdir + output_file