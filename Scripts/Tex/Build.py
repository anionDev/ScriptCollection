from argparse import ArgumentParser
import subprocess
parser = ArgumentParser()
parser.add_argument("-pdf", dest="pdflatexfile", help="pdfLatex file with full path", default="pdflatex")
parser.add_argument("-tex", dest="texfile", help="texFile which should be compiled", default="document.tex")
args = parser.parse_args()
pdfLatexArgument="\"\input{" + args.texfile + "}\" -synctex=1 -interaction=nonstopmode -job-name cheatsheet"
subprocess.call(args.pdflatexfile + " " + pdfLatexArgument)
