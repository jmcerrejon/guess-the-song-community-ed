#!/bin/bash

# You need ffmpeg installed for this script to work.
# This script converts all MP4 and M4A files in the specified directory to MP3 format.
# Usage: ./mp42mp3.sh

find ../data -type f \( -name "*.mp4" -o -name "*.m4a" \) -exec bash -c '
    input="$1"
    if [[ $input == *.mp4 ]]; then
        output="${input%.mp4}.mp3"
    else
        output="${input%.m4a}.mp3"
    fi
    ffmpeg -i "$input" "$output" && echo "Converted: $input to $output" >> conversion.log
' _ {} \;
