
import sys
import re
import ast
import time

animation='goal:S18#red'
# Segment(s) to be stroked
pattern=re.compile("^goal:.*$")
if pattern.match(animation) :
    CStrip.Segment(50,COpen,3,animation.split(':')[1],False)

