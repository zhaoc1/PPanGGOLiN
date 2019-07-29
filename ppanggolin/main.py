#!/usr/bin/env python3
#coding:utf-8
# PYTHON_ARGCOMPLETE_OK

#default libraries
import sys
assert sys.version_info >= (3, 6)#minimum is python3.6
import argparse
import time
import logging
import os
import resource

#libraries to be installed
# from tqdm import tqdm
import psutil
import pkg_resources

try:
    import argcomplete
except ImportError:
    pass

#local modules
import ppanggolin.partition
import ppanggolin.create
import ppanggolin.annotate
import ppanggolin.cluster

def requirements():
    """
        Checks if the tools and libraries required for each submodule are installed.
    """
    pass

def cmdLine():
    parser = argparse.ArgumentParser(description = "Depicting microbial species diversity via a Partitioned PanGenome Graph Of Linked Neighbors", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','--version', action='version', version='%(prog)s ' + pkg_resources.get_distribution("ppanggolin").version)
    subparsers = parser.add_subparsers( metavar = "", dest="subcommand")
    subparsers.required = True#because python3 sent subcommands to hell apparently
    subs = set([])#subparsers
    subs.add(ppanggolin.annotate.syntaSubparser(subparsers))
    subs.add(ppanggolin.cluster.clusterSubparser(subparsers))
    subs.add(ppanggolin.partition.partitionSubparser(subparsers))
    subs.add(ppanggolin.create.createSubparser(subparsers))
    #TODO :
    # Figures subparser
    # Format subparser

    for sub in subs:#add options common to all subcommands
        common = sub.add_argument_group(title = "Common options")
        common.add_argument("--tmpdir", required=False, type=str, default="/dev/shm", help = "directory for storing temporary files (default : /dev/shm)")
        common.add_argument('-o','--output', required=False, type=str, default="ppanggolin_output"+time.strftime(
            "_DATE%Y-%m-%d_HOUR%H.%M.%S", time.localtime())+"_PID"+str(os.getpid()), help="Output directory")
        common.add_argument("--verbose",required=False, type=int,default=1,choices=[0,1,2], help = "Indicate verbose level (0 for warning and errors only, 1 for info, 2 for debug)")
        common.add_argument("-c","--cpu",required = False, default = 1,type=int, help = "Number of available cpus")
        common.add_argument('-f', '--force', action="store_true", help="Force writing in existing output directory")
        common.add_argument("-se", "--seed", type = int, default = 42, help="seed used to generate random numbers")
        common.add_argument("--memory", required=False, type=int, default=int(4 * psutil.virtual_memory().total / 5), help="Max amount of allowed RAM. Default is 4/5 of the system's RAM. Will work only for the python part of the program. The C part might use more without raising an error.")

        if len(sys.argv) == 2 and sub.prog.split()[1] == sys.argv[1]:
            sub.print_help()
            exit(1)
   
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    if args.subcommand == "annotate":
        if args.fasta is None and args.gff is None:
            raise Exception( "You must provide at least a file with the --fasta option to annotate from sequences, or a file with the --gff option to load annotations from.")
        if args.fasta is not None and args.gff is not None:
            raise Exception("You must provide just one of --fasta or --gff file. You can't both annotate and read annotations.")
    return args

def main():
    args = cmdLine()
    if args.verbose == 2:
        level = logging.DEBUG#info, debug, warnings and errors
    elif args.verbose == 1:
        level = logging.INFO#info, warnings and errors
    elif args.verbose == 0:
        level = logging.WARNING#only warnings and errors
    logging.basicConfig(stream=sys.stdout, level = level, format = '%(asctime)s %(filename)s:l%(lineno)d %(levelname)s\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    elif not args.force:
        logging.getLogger().error(f"{args.output} already exists. Use -f if you still want to (over)write files in this directory.")
        exit(1)

    fhandler = logging.FileHandler(filename = args.output + "/PPanGGOLiN.log",mode = "w")
    fhandler.setFormatter(logging.Formatter(fmt = "%(asctime)s %(filename)s:l%(lineno)d %(levelname)s\t%(message)s", datefmt='%Y-%m-%d %H:%M:%S'))
    fhandler.setLevel(level if level != logging.WARNING else logging.INFO)
    logging.getLogger().addHandler(fhandler)

    rsrc = resource.RLIMIT_DATA
    _, hard = resource.getrlimit(rsrc)
    resource.setrlimit(rsrc, (args.memory, hard))  # limiting allowed RAM

    logging.getLogger().info("Command: "+" ".join([arg for arg in sys.argv]))
    logging.getLogger().info("PPanGGOLiN version: "+pkg_resources.get_distribution("ppanggolin").version)

    if args.subcommand == "annotate":
        ppanggolin.annotate.launch(args)
    elif args.subcommand == "cluster":
        ppanggolin.cluster.launch(args)
    elif args.subcommand == "create":
        ppanggolin.create.launch(args)
    elif args.subcommand == "partition":
        pass

if __name__ == "__main__":
    main()