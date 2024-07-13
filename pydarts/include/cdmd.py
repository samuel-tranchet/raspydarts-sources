#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random

"""
Class used to send informations to dmd
"""

class Cdmd():
    """
    Class used to send messages to DMD
    """

    def __init__(self, logs, event, file_class):
        self.dart = { 0:'', 1:'', 2:''}
        self.event = event
        self.logs = logs
        self.file_class = file_class

        self.init_insults()
        self.insults = False

    def init_insults(self):
        """
        Load insults' file
        """

        self.insults_tab = []
        insults_file = self.file_class.get_full_filename('insults', 'text')
        if insults_file is not None:
            try:
                with open(f'{insults_file}', 'r') as insults:
                    text = insults.readlines()
                insults.close()
                self.insults_tab = text
            except:
                pass

    def send_insult(self, firstname=None):
        """
        Send soft insult to DMD
        """
        if len(self.insults_tab) > 0:
            index = random.randint(0, len(self.insults_tab) - 1)
            self.send_text(self.insults_tab[index].replace('\n', '').replace('{}', firstname))

    def send(self, msg):
        """
        Send message using event class
        """
        self.event.publish(msg, limit="DMD")

    def shutdown(self):
        """
        Message to send in order to shutdown the rpi
        """
        self.send('shutdwn|')

    def send_text(self, text, tempo=None, sens=None, iteration=None):
        """
        Function used to send text to dmd
        """

        if sens :
            if iteration :
                msg = 'msgmovebcl|{}'
            else :
                msg = 'msgmove|{}'
        else :
            if len(text) > 22 :
                msg = 'msgmove|{}'
                sens = 'left'
            else :
                msg = 'msg|{}'

        msg = msg.format(text)
        if sens :
            msg += f'|{sens}'

        if iteration :
            msg += f'|{iteration}'

        if tempo :
            msg += f'|{tempo}'

        self.send(msg)

    def send_score(self, dart, touch):
        """
        Function used to send score to dmd
        """

        if dart == 1:
            self.dart[0] = touch
            text = f'score|{touch} - X - X'
        elif dart == 2:
            self.dart[1] = touch
            text = f'score|{self.dart[0]} - {touch} - X'
        elif dart == 3:
            self.dart[2] = touch
            text = f'score|{self.dart[0]} - {self.dart[1]} - {touch}'
        else:
            return

        self.send(text)
