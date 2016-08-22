import sys #handling arguments passed to function
import glob #file path handling
import os #checking files and writing to/from files
import re #regex matching
import multiprocessing as mp #drastic speedups when implemented on an i7-4710HQ
import subprocess
from subprocess import PIPE
from core.funcs import *

path = ''
outpath = ''

def genxhtml(filename):
    global outpath
    fname = os.path.basename(filename)
    outfname = outpath + (os.path.splitext(fname)[0]+'.xhtml')
    if os.path.isfile(outfname):
        print("{}: Already generated".format(filename))
        return ""
    # print("{}: Start".format(filename))
    with open(filename, mode='r', encoding='latin-1') as f1:
        text = f1.read()
    text = removecomments(text)
    #series of regex expressions
    docbody = re.search(r'(?s)\\begin\{document\}.*?\\end\{document\}',text).group(0)
    if not docbody:
        print("{}: Error: \\begin{document} error".format(filename))
        return("{}: Error: \\begin{document} error".format(filename))
    body = grabmath(docbody)
    packages = re.findall(r'\\usepackage(?:\[.*?\])?\{.*?\}',text)
    docclass = re.search(r'\\documentclass(?:\[.*?\])?\{.*?\}',text)
    if(docclass):
        docclass = docclass.group(0)+'\n'
    else:
        docclass = '\\documentclass{article}\n'
    preamble = [docclass] + packages + ['\\begin{document}\n']
    postamble = ["\\end{document}"]
    output = '\n'.join(preamble+body+postamble)
    try:
        proc = subprocess.Popen(["latexml", "-"], stderr = PIPE, stdout = PIPE, stdin = PIPE)
        stdout, stderr = proc.communicate(output.encode(), timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        print("{}: MathML conversion failed - timeout".format(filename))
        return "{}: MathML conversion failed - timeout".format(filename)
    except:
        print("{}: Conversion failed".format(filename))
        return "{}: Conversion failed".format(filename)
    try:
        proc = subprocess.Popen(["latexmlpost", "--format=xhtml", "-"], stderr = PIPE, stdout = PIPE, stdin = PIPE)
        stdout2, stderr = proc.communicate(stdout, timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        print("{}: MathML postprocessing failed - timeout".format(filename))
        return "{}: MathML postprocessing failed - timeout".format(filename)
    if len(stdout2.strip())==0:
        print("{}: Conversion failed".format(filename))
        return("{}: Conversion failed".format(filename))
    with open(outfname,'w') as fh:
        fh.write(stdout2.decode())
    # print("{}: Finish".format(filename))
    return ""

def main():
    origdir = os.getcwd()
    global path
    global outpath
    if len(sys.argv)==1:
        print("Error: must pass in one or more valid directories")
    path = os.path.join(str(sys.argv[1]),'')
    if not os.path.isdir(path):
        print("Error: {} is not a valid directory".format(x))
        sys.exit()
    print("Beginning processing of {}".format(path))
    path = os.path.abspath(path) + '/'
    print("Generating list of files with math...")
    filelist = getmathfiles(path)
    print("Generation complete.")
    if len(sys.argv)==3:
        outpath = os.path.join(sys.argv[2],'')
    else:
        outpath = path[:-1] + '_converted/'
    outpath = os.path.abspath(outpath) + '/'
    if not os.path.exists(outpath):
        os.makedirs(outpath)
    os.chdir(outpath)
    pool = mp.Pool(processes=mp.cpu_count())
    print("Initialized {} threads".format(mp.cpu_count()))
    print("Beginning processing...")
    outlist = pool.map(genxhtml,filelist)
    with open(outpath[:-1]+".log",'w') as fh:
        for message in outlist:
            if len(message)>0:
                fh.write(message)
    pool.close()
    pool.join()
    os.chdir(origdir)


if __name__ == '__main__':
    main()
