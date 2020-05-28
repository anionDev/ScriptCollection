"""
Tested on: Windows
This program comes with absolutely no warranty.
Commands which must be available in the path-variable:
-ffmpeg
-ffprobe
-montage (from ImageMagick)
-epew
"""

import argparse
import uuid
from pathlib import Path
import datetime

def calculate_lengh_in_seconds(file:str,wd:str):
    argument='-v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "'+file+'"'
    return float(execute_and_raise_exception_if_exit_code_is_not_zero("ffprobe",argument,wd)[1])

def create_thumbnails(file:str,length_in_seconds:float,amount_of_images:int,wd:str):
    rrp=length_in_seconds/(amount_of_images-2)
    argument='-i "'+file+'" -r 1/'+str(rrp)+' -vf scale=-1:120 -vcodec png '+tempname_for_thumbnails+'-%002d.png'
    execute_and_raise_exception_if_exit_code_is_not_zero("ffmpeg",argument,wd)

def create_thumbnail(outputfilename:str,wd:str,length_in_seconds:float):
    duration=datetime.timedelta(seconds=length_in_seconds)
    info=timedelta_to_simple_string(duration)
    argument='-title "'+outputfilename+" ("+info+')" -geometry +4+4 '+tempname_for_thumbnails+'*.png "'+outputfilename+'.png"'
    execute_and_raise_exception_if_exit_code_is_not_zero("montage",argument,wd)

def SCGenerateThumbnail_cli():
    parser = argparse.ArgumentParser(description='Generate thumpnails for video-files')
    parser.add_argument('file', help='Input-videofile for thumbnail-generation')

    args = parser.parse_args()
    tempname_for_thumbnails="t"+str(uuid.uuid4())


    amount_of_images=16
    file=args.file
    filename=os.path.basename(file)
    folder=os.path.dirname(file)
    filename_without_extension=Path(file).stem

    try:
        length_in_seconds=calculate_lengh_in_seconds(filename,folder)
        create_thumbnails(filename,length_in_seconds,amount_of_images,folder)
        create_thumbnail(filename_without_extension,folder,length_in_seconds)
    finally:
        for thumbnail_to_delete in Path(folder).rglob(tempname_for_thumbnails+"-*"):
            file=str(thumbnail_to_delete)
            os.remove(file)

if __name__ == '__main__':
    SCGenerateThumbnail_cli()
