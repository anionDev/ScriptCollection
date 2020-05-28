"""
Tested on: Windows
This program comes with absolutely no warranty.
This program requires PyPDF2 (you can install PyPDF2 using 'pip install PyPDF2')
"""
import argparse
from PyPDF2 import PdfFileMerger

def SCMergePDFs_cli():

    parser = argparse.ArgumentParser(description='Takes some pdf-files and merge them to one single pdf-file. Usage: "python MergePDFs.py myfile1.pdf,myfile2.pdf,myfile3.pdf result.pdf"')
    parser.add_argument('files', help='Comma-separated filenames')
    parser.add_argument('outputfile', help='File for the resulting pdf-document')
    args = parser.parse_args()

    #TODO add wildcard-option
    files = args.files.split(',')
    pdfFileMerger = PdfFileMerger()
    for file in files:
        pdfFileMerger.append(file)
    pdfFileMerger.write(args.outputfile)
    pdfFileMerger.close()

if __name__ == '__main__':
    SCMergePDFs_cli()
