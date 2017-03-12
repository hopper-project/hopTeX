"""enumerate_docs.py - substitutes math equations in LaTeX documents with
document IDs from an equation tsv
(generated by enumerate_eqs/enumerate_inline_eqs)
"""
import argparse
import os
import multiprocessing as mp
from core.funcs import *
from multiprocessing import Manager
import multiprocessing as mp
from glob import glob
import shutil
import gc

def substitute_eqid(filename):
    """Substitutes equations in document with their respective inline
    equations"""
    global eqdict
    global outpath
    global inline
    no_math = True
    print(filename)
    with open(filename,mode='r',encoding='latin-1') as fh:
        text = fh.read()
    if(inline):
        textlist = grab_inline_math(text,split=True)
        for i, x in enumerate(textlist):
            if x in eqdict:
                textlist[i] = eqdict[x]
                no_math = False
        if no_math:
            print("{}: no inline math".format(filename))
            return
        newtext = ''.join(textlist)
    else:
        textlist = grab_math(text,split=True)
        for i, x in enumerate(textlist):
            if is_math(x):
                if flatten_equation(x) in eqdict:
                    textlist[i] = eqdict[flatten_equation(x)]
                    no_math = False
                else:
                    textlist[i] = textlist[i].strip()
        if no_math:
            return
        newtext = '\n'.join(textlist)
    if outpath:
        filename = os.path.join(outpath,os.path.basename(filename))
    with open(filename,mode='w',encoding='utf-8') as fh:
        fh.write(newtext)

def main():
    global eqdict
    global outpath
    global inline
    parser = argparse.ArgumentParser(description=\
    'Usage for equation enumeration')
    parser.add_argument("tsv",
    help="Path to .tsv of enumerated equations (output of enumerateeqs.py)")
    parser.add_argument("--parent", action='store_true',
    help="Use flag if the specified directory is the parent of .tex file directories")
    parser.add_argument("directory",help="Path to directory of .tex files, or demacro (if the flag is specified)")
    parser.add_argument("--outpath",help="Path to output directory (WARNING: if this flag is not used with an output directory, it will overwrite the .tex files in place)")
    parser.add_argument("--inline", action='store_true', help="Use flag if enumerating inline equations")
    args = parser.parse_args()
    tsv = os.path.abspath(args.tsv)
    directory = os.path.join(os.path.abspath(args.directory),'')
    if(args.outpath):
        outpath = os.path.join(os.path.abspath(args.outpath),'')
    else:
        outpath = directory
    parent = args.parent
    inline = args.inline
    print("Generating equation dictionary...")
    eqdict = {}
    counter = 0
    if inline:
        with open(tsv,mode='r',encoding='latin-1') as fh:
            for line in fh:
                eqid, equation = line.strip().split('\t')
                equation = equation.encode().decode('unicode_escape').strip()
                if equation not in eqdict:
                    eqdict[equation] = eqid
                counter += 1
    else:
            with open(tsv,mode='r',encoding='latin-1') as fh:
                for line in fh:
                    contents = line.strip().split('\t')
                    if len(contents)==2:
                        eqid, equation = contents
                        equation  = unmask(equation)
                        eqdict[flatten_equation(equation)] = eqid
                    elif len(contents)==3:
                        eqid, sub_ids, equation = contents
                        equation = unmask(equation)
                        eqdict[flatten_equation(equation)] = eqid
    print("Equation dictionary loaded.")
    print("{} entries".format(len(eqdict)))
    pool = mp.Pool(mp.cpu_count())
    if(parent):
        filelist = []
        print("Iterating over folders in {}".format(directory))
        if outpath != directory:
            folderlist = next(os.walk(directory))[1]
            for subfolder in folderlist:
                print("Copying {}".format(subfolder))
                shutil.copytree(os.path.join(directory,subfolder),os.path.join(outpath,subfolder))
        else:
            outpath = directory
        for root, folders, files in os.walk(outpath):
            for filename in files:
                filelist.append(os.path.join(root,filename))
        pool.map(substitute_eqid,filelist)
        pool.close()
        pool.join()
    else:
        if not os.path.exists(outpath):
            os.makedirs(outpath)
        print("Finding all .tex files...")
        filelist = gettexfiles(directory)
        print("Found {} files".format(len(filelist)))
        print("Writing files...")
        pool.map(substitute_eqid,filelist)
        pool.close()
        pool.join()

if __name__ == '__main__':
    main()
