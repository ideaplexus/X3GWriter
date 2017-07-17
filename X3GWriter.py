# Copyright (c) 2016 Ghostkeeper
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger
from UM.Application import Application
import io
import subprocess
import os

class X3GWriter(MeshWriter):
    def __init__(self):
        super().__init__()
        self._gcode = None

    ##  Write the X3G data to a stream.
    #
    #   \param stream The stream to write X3G data to.
    #   \param nodes A sequence of nodes to write to the stream.
    #   \param mode The output mode to use. This is ignored, since it has no
    #   meaning.
    def write(self, stream, nodes, mode = MeshWriter.OutputMode.TextMode):
        #Get the g-code.
        scene = Application.getInstance().getController().getScene()
        gcode_list = getattr(scene, "gcode_list")
        if not gcode_list:
            return False

        #Find an unused file name to temporarily write the g-code to.
        file_name = stream.name
        if not file_name: #Not a file stream.
            Logger.log("e", "X3G writer can only write to local files.")
            return False
        file_directory = os.path.dirname(os.path.realpath(file_name)) #Save the tempfile next to the real output file.
        i = 0
        temp_file = file_directory + "/output" + str(i) + ".gcode"
        while os.path.isfile(temp_file):
            i += 1
            temp_file = file_directory + "/output" + str(i) + ".gcode"

        #Write the g-code to the temporary file.
        try:
            with open(temp_file, "w", -1, "utf-8") as f:
                for gcode in gcode_list:
                    f.write(gcode)
        except:
            Logger.log("e", "Error writing temporary g-code file %s", temp_file)
            _removeTemporary(temp_file)
            return False

        #Call the converter application to convert it to X3G.
        Logger.log("d", "App path: %s", os.getcwd())
        Logger.log("d", "File name: %s", file_name)
        binary_path = os.path.dirname(os.path.realpath(__file__))
        binary_filename = binary_path + r"\cura_x3g.exe"
        command = [binary_filename, "-p", "-m", "r1d", "-c", binary_path + r"\cfg.ini", temp_file, file_name]
        safes = [os.path.expandvars(p) for p in command]
        Logger.log("d", "Command: %s", str(command))
        stream.close() #Close the file so that the binary can write to it.
        try:
            process = subprocess.Popen(safes, shell=True)
            process.wait()
            output = process.communicate(b'y')
            Logger.log("d", str(output))
        except Exception as e:
            Logger.log("e", "System call to X3G converter application failed: %s", str(e))
            _removeTemporary(temp_file)
            return False

        _removeTemporary(temp_file)
        return True

##  Removes the temporary g-code file that is an intermediary result.
#
#   This should be called at the end of the write, also if the write failed.
#
#   \param temp_file The URI of the temporary file.
def _removeTemporary(temp_file):
    try:
        os.remove(temp_file)
    except:
        Logger.log("w", "Couldn't remove temporary file %s", temp_file)