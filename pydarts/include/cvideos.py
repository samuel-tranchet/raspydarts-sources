#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Class used to play videos
"""

from math import log as math_log
import subprocess as subp

class Videos():
    """
    Module used to play videos
    """

    def __init__(self, logs, c_file, level=0, volume=70, multiplier=1):
        self.logs = logs
        self.level = int(level)
        self.volume = volume
        self.file = c_file
        self.multiplier = multiplier
        self.set_volume(volume)

    def set_level(self, level):
        """
        Set video level
        """
        self.logs.log("DEBUG", f"Set video level to {level}")
        self.level = int(level)

    def set_volume(self, volume):
        """
        Set volume
        """
        log = int(4000 - math_log(max(int(volume / 3 * self.multiplier), 1), 10) * 2000)
        self.logs.log("DEBUG", f"Set volume to {-log}")

        self.volume = -log

    def play_video(self, video, wait=False):
        """
        Play video
        """
        if video is None:
            return False

        self.logs.log("DEBUG", f"Play {video}")
        msg = f'omxplayer --vol {self.volume} -o alsa "{video}"'

        self.logs.log("DEBUG", f"{msg}")
        if wait:
            with subp.Popen(['omxplayer', '--vol', f'{self.volume}', '-o', 'alsa', f'{video}'], stdout=subp.DEVNULL, stderr=subp.DEVNULL) as process :
                process.wait()
        else:
            with subp.Popen(['omxplayer', '--vol', f'{self.volume}', '-o', 'alsa', f'{video}'], stdout=subp.DEVNULL, stderr=subp.DEVNULL):
                pass
        return True

    ################################################################
    ### Methode pour lire un plusieurs videos
    ################################################################
    def play_videos(self, videos):
        """
        Play a list of videos
        """

        self.play_video(videos.join(' '))

    ################################################################
    ### Methode pour lire les videos standard et speciales
    ################################################################
    def play_show(self, darts, hit, play_special=False):
        """
        Identify the special move, find the video and play it
        """

        if self.level < 1:
            return False

        video = None
        if 'X' not in darts and None not in darts:
            video = self.special_move(darts[0], darts[1], darts[2], play_special)
            if video is not None:
                self.play_video(self.file.get_full_filename(video, 'videos'), wait=True)
                return True

        if video is None:   # and hit in ('SB', 'DB'):
            video = self.file.get_full_filename(file_name=hit, file_type='videos')

        if video is None and hit in ('SB', 'DB', 'T20', 'T19', 'T18', 'T17'):
            video = self.file.get_full_filename(file_name='big_score', file_type='videos')

        if video is not None:
            self.play_video(video, wait=True)
            return True

        return False

    def dart_value(self, dart, mult=False):
        """
        Extract number from dart stroke
        """
        if dart == 'SB':
            return 25

        if dart == 'DB':
            return 50

        multiplier = 1
        if mult:
            if dart[0] == 'D':
                multiplier = 2
            elif dart[0] == 'T':
                multiplier = 3

        return int(dart[1::]) * multiplier

    def special_move(self, dart1, dart2, dart3, play_special):
        """
        Is ther any special video according to special move ?
        """

        special_move = None
        darts = [dart1.upper(), dart2.upper(), dart3.upper()]
        try:
            sorted_darts = darts
            sorted_darts.sort(key=self.dart_value)
        except: # pylint: disable=bare-except
            sorted_darts = []

        somme = 0
        for dart in darts:
            if dart == 'SB':
                somme += 25
            elif dart == 'DB':
                somme += 50
            elif dart is not None and dart[0] in ['S', 'D', 'T']:
                somme += self.dart_value(dart, True)

        self.logs.log("DEBUG", f"Search for move ({play_special}/{self.level}) : {sorted_darts}")

        if all(x == 'T20' for x in darts):
            special_move = 'MAXIMUM_TON_80'

        elif play_special and self.level == 2:

            # DEVIL = S6 - S6 - S6
            if all(x == 'S6' for x in darts):
                special_move = 'DEVIL'

            # TRIPLE DEVIL = T6 - T6 - T6
            elif all(x == 'T6' for x in darts):
                special_move = 'DEVIL_TRIPLE'

            # BREAKFAST (CHIPS/CLASSIC) = S5 - S20 - S1 (peu importe l'ordre)
            elif sorted_darts == ['S1', 'S5', 'S20']:
                special_move = 'BREAKFAST'

            # CHAMPAGNE BREAKFAST (GRAND SLAM) = T5 - T1 - T20 (peu importe l'ordre)
            elif sorted_darts == ['T1', 'T5', 'T20']:
                special_move = 'CHAMPAGNE_BREAKFAST'

            # ROUND OF TERMS = T1 - T1 - T1
            elif dart1[0:1] == 'T' and dart2[0:1] == 'T' and dart3[0:1] == 'T':
                special_move = 'ROUND_OF_TERMS'

            # BAG (BUCKET) OF NAIL = S1 - S1- S1
            elif all(x == 'S1' for x in darts):
                special_move = 'BUCKET_OF_NAIL'

            # NOT OLD = S5 - S20 - S12 (peu importe l'ordre)
            elif sorted_darts == ['S5', 'S12', 'S20']:
                special_move = 'NOT_OLD'

        if special_move is not None:
            return special_move

        if all(x is None for x in darts):
            special_move = 'WHITE_HORSE'

        # BLACK HAT = DB - DB - DB
        elif all(x == 'DB' for x in darts):
            special_move = 'BLACK_HAT_THREE_IN_THE_BLACK'

        # RED HAT = SB - SB - SB
        elif all(x == 'SB' for x in darts):
            special_move = 'RED_HAT'

        # HAT TRICK = SB - DB - SB (3 bulls peu importe lesquelles)
        elif dart1 in ['SB', 'DB'] and dart2 in ['SB', 'DB'] and dart3 in ['SB', 'DB']:
            special_move = 'HAT_TRICK'

        # THREE IN A BED = 3 fois le meme segment
        elif all(x == dart1 for x in darts):
            special_move = 'THREE_IN_A_BED'

        # LOW TON = tot >= 100 & <= 150
        elif 99 < somme < 151:
            special_move = 'LOW_TON'

        # HIGH TON = tot >= 151 & <= 179
        elif 150 < somme < 180:
            special_move = 'HIGH_TON'

        # BAIL OUT = La 3eme flechette marque un triple eleve
        elif dart3 in ['T20', 'T19', 'T18', 'T17'] and play_special and self.level == 2:
            special_move = 'BAIL_OUT'

        return special_move
