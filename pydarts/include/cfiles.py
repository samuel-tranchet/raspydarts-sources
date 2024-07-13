"""
Class used for file identification
"""

import random
import sys
from os import listdir
from os.path import isdir, isfile, getsize

class Cfile():
    """
    File class
    """

    def __init__(self, config, logs, theme=None):
        self.logs = logs
        self.config = config
        self.reset_theme(theme)

    def reset_theme(self, theme):
        self.files = {}
        self.theme = theme
        self.theme_dir = f'{self.config.user_dir}/themes/{theme}'

    def is_dir(self, file_name=None, file_type=None):
        if file_type is None or file_name is None:
            self.logs.log("WARNING", f"file_type ({file_type}) or file_name ({file_name}) is None.")
            return False

        if isfile(file_name):
            return False

        stack = self.files.get(f'{file_name}-{file_type}', None)
        if isinstance(stack, str) or isinstance(stack, list):
            return True

        config = self.config.dirs.get(file_type, None)
        if config is None:
            self.logs.log("WARNING", f"Unknown {file_type} file type")
            return False

        sub_dir = config[0]
        extensions = config[1]

        theme_dir = f'{self.theme_dir}/{sub_dir}/{file_name}'
        personnal_dir = f'{self.config.user_dir}/{sub_dir}/{file_name}'
        official_dir = f'{self.config.root_dir}/{sub_dir}/{file_name}'

        if isdir(theme_dir) and len(listdir(theme_dir)) > 0:
            return True
        elif isdir(personnal_dir) and len(listdir(personnal_dir)) > 0:
            return True
        elif isdir(official_dir) and len(listdir(official_dir)) > 0:
            return True

        return False

    def get_full_filename(self, file_name=None, file_type=None):
        """
        Return full file name (absolute directory / file_name . extension if found
        None if not found
        Seach in personnal directory then in official directory
        """

        #self.logs.log("WARNING", f"get_full_filename called by {sys._getframe().f_back.f_code.co_name}")
        #self.logs.log("WARNING", f"search for {file_name} of type {file_type}")

        if file_type is None or file_name is None:
            self.logs.log("WARNING", f"file_type ({file_type}) or file_name ({file_name}) is None.")
            return None

        if isfile(file_name):
            #self.logs.log("WARNING", f"{file_name} is already a file. No need to search more.")
            return file_name

        config = self.config.dirs.get(file_type, None)
        if config is None:
            self.logs.log("WARNING", f"Unknown {file_type} file type")
            return None

        sub_dir = config[0]
        extensions = config[1]

        theme_dir = f'{self.theme_dir}/{sub_dir}'

        official = True
        for extension in extensions:
            full_file_name = f"{file_name.replace(f'.{extension}', '')}.{extension}"
            #if file_type != 'fonts':
            #    self.logs.log("DEBUG", f"Search for {theme_dir}/{full_file_name} null size file")
            if isfile(f'{theme_dir}/{full_file_name}') and getsize(f'{theme_dir}/{full_file_name}') == 0:
            #   self.logs.log("DEBUG", f"Null size file found for {theme_dir}/{full_file_name}")
                official = False
                return None

        # Search for a folder in personnalfolder
        theme_dir = f'{self.theme_dir}/{sub_dir}/{file_name}'
        personnal_dir = f'{self.config.user_dir}/{sub_dir}/{file_name}'
        official_dir = f'{self.config.root_dir}/{sub_dir}/{file_name}'

        stack = self.files.get(f'{file_name}-{file_type}', None)

        if stack is None or len(stack) == 0:

            found_dir = None
            if isdir(theme_dir) and len(listdir(theme_dir)) > 0:
                found_dir = theme_dir
            elif isdir(personnal_dir) and len(listdir(personnal_dir)) > 0:
                found_dir = personnal_dir
            elif isdir(official_dir) and len(listdir(official_dir)) > 0 and official:
                found_dir = official_dir

            if found_dir is not None:
                stack = listdir(found_dir)
                self.files[f'{file_name}-{file_type}'] = [f'{found_dir}/{s}' for s in stack]
                stack = self.files[f'{file_name}-{file_type}']

        if isinstance(stack, str):
            return stack
        elif isinstance(stack, list):
            random_file_index = random.randint(0, len(stack) - 1)
            stacked_file = stack.pop(random_file_index)
            self.files[f'{file_name}-{file_type}'] = stack
            self.logs.log("DEBUG", f"Return {stacked_file} from stack")
            return stacked_file

        theme_dir = f'{self.theme_dir}/{sub_dir}'
        personnal_dir = f"{self.config.user_dir}/{sub_dir}"
        official_dir = f"{self.config.root_dir}/{sub_dir}"

        for extension in extensions:
            full_file_name = f"{file_name.replace(f'.{extension}', '')}.{extension}"

            # Search for file first
            # Search in theme first
            # then in personnal folder
            # else in official folder
            #if file_type != 'fonts':
            #    self.logs.log("DEBUG", f"Search for {theme_dir}/{full_file_name}")
            if isfile(f'{theme_dir}/{full_file_name}'): #and getsize(f'{theme_dir}/{full_file_name}') > 0:
            #    if file_type != 'fonts':
            #        self.logs.log("DEBUG", f"Return {theme_dir}/{full_file_name} from 1")
                return f'{theme_dir}/{full_file_name}'

            #if file_type != 'fonts':
            #    self.logs.log("DEBUG", f"Search for {personnal_dir}/{full_file_name}")
            if isfile(f'{personnal_dir}/{full_file_name}') and getsize(f'{personnal_dir}/{full_file_name}') > 0:
            #    if file_type != 'fonts':
            #        self.logs.log("DEBUG", f"Return {theme_dir}/{full_file_name} from 2")
                return f'{personnal_dir}/{full_file_name}'

            # Else, in official folder
            #if file_type != 'fonts':
            #    self.logs.log("DEBUG", f"Search for {official_dir}/{full_file_name}")
            if isfile(f'{official_dir}/{full_file_name}') and getsize(f'{official_dir}/{full_file_name}') > 0:
            #    if file_type != 'fonts':
            #        self.logs.log("DEBUG", f"Return {theme_dir}/{full_file_name} from 3")
                return f'{official_dir}/{full_file_name}'

        self.logs.log("DEBUG", "Return None")
        return None
