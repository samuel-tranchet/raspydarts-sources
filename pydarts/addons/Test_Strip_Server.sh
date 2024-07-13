#!/bin/sh

set -euxv

PIN=12
NBPIXELS=72

# Be careful. CAhnge it only if you know what you do
DMA_CHANNEL=10

python3 StripLeds_Server.py $DMA_CHANNEL 'raspydarts/stripLeds' $PIN $NBPIXELS .5

