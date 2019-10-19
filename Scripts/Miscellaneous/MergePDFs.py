"""
Tested on: Windows
This program comes with absolutely no warranty.
This program requires PyPDF2 (you can install PyPDF2 using 'pip install PyPDF2')
"""
import argparse
from PyPDF2 import PdfFileMerger

parser = argparse.ArgumentParser(description='Takes some pdf-files and merge them to one single pdf-file. Usage: python MergePDFs.py myfile1.pdf,myfile2.pdf,myfile3.pdf result.pdf')
parser.add_argument('files', help='Comma-separated filenames without any blank')
parser.add_argument('outputfolder', help='Folder where the files are stored which should be hashed')
args = parser.parse_args()

files = args.files.split(',')
pdfFileMerger = PdfFileMerger()
for file in files:
    pdfFileMerger.append(file)
pdfFileMerger.write(args.outputfolder)
pdfFileMerger.close()
