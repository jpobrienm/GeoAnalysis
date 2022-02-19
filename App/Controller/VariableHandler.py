import os
import re


class VariableHandler:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def gather_var(self, var_name:str, indicator="", file_type=".tif"):
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(file_type):
                    file_regex = re.split("[._ ]", file.lower())
                    if file_regex[0] == var_name and (indicator in file_regex[1]):
                        return os.path.join(root, file)
        return "no var"


#path = r"C:\Users\jpobr\Desktop\AAA\cropped"
#var = VariableHandler(path)
#a = var.gather_var("hsi")
#print(a)
