import sys
import getopt
import glob
import logging

from compiler import convert


def print_help():
    VERSION = 0.1
    print(
        f'''
yang2owl version {VERSION}: convert yang modules to owl ontologies

usage: yang2owl [-o OUTFILE] [-f FORMAT] [-v LEVEL] [-t TARGET] <-n NAMESPACE> YANG_MODULES

\t-n NAMESPACE\tNamespace of the output ontology, mandatory argument
\t-o OUTFILE:\tPlace the output into OUTFILE, default to 'ontology.owl';
\t-f FORMAT:\tSpecify ontology format. Supported formats are rdfxml and ntriples;
\t-v LEVEL:\tSelect verbosity LEVEL between 0 (least verbose, default), 1 or 2 (most verbose);
\t-t TARGET:\tSelect target modules to parse, default ALL 
\tYANG_MODULES:\tInput yang modules, glob supported;

==============================================================================================================
Examples:

- Convert single yang module to owl ontology:
\tyang2owl -n http://example.org/owl/module module.yang

- Convert all yang module in directory modules to owl ontology, save with ntriples with filename module.owl
\tyang2owl -n http://example.org/owl/module -o module.owl -f ntriples modules/*.yang

- Convert xyz module to owl ontology, supply all modules in the directory to resolve external dependencies
\tyang2owl -n http://example.org/owl/module -o module.owl -t xyz modules/*.yang

- Convert xyz and abc modules to owl ontology, supply all modules in the directory to resolve external dependencies
\tyang2owl -n http://example.org/owl/module -o module.owl -t xyz -t abc modules/*.yang
        '''
    )


def __main_cli(argv):
    ifiles = []
    ontology_format = None
    verbosity = logging.ERROR
    output = None
    namespace = None
    targets = []

    try:
        opts, args = getopt.getopt(argv, "ht:o:f:v:n:")
    except getopt.GetoptError as e:
        print(f'Error: {e}')
        return 2

    for arg in args:
        for file in glob.glob(arg, recursive=True):
            try:
                open(file, 'r').close()
                ifiles.append(file)
            except IOError:
                print(f'Warning: Cannot read {file}, skipping')

    for opt, arg in opts:

        if opt == '-h':
            print_help()
            return 0

        elif opt == "-o":
            if output is None:
                try:
                    open(arg, 'w').close()
                    output = arg
                except IOError:
                    print(f'Error: Cannot write to {arg}')
            else:
                print(f'Error: Multiple output files defined')
                return 2

        elif opt == '-t':
            targets.append(arg)

        elif opt == '-v':
            if arg not in ['0', '1', '2']:
                print(f'Error: Illegal verbosity value')
                return 2
            else:
                if arg == '0':
                    verbosity = logging.WARNING
                elif arg == '1':
                    verbosity = logging.INFO
                elif arg == '2':
                    verbosity = logging.DEBUG
            logging.basicConfig(level=verbosity)

        elif opt == '-n':
            namespace = arg

        elif opt == '-f':
            if arg not in ['rdfxml', 'ntriples']:
                print(f'Error: Illegal output format')
                return 2
            else:
                ontology_format = arg

    logging.debug(f'Input files are {ifiles}')
    if len(ifiles) == 0:
        print(f'Error: Missing input files')
        return 2

    logging.debug(f'Namespace format is {namespace}')
    if namespace is None:
        print(f'Error: Missing namespace')
        return 2

    if ontology_format is None:
        ontology_format = 'rdfxml'
    logging.debug(f'Output format is {ontology_format}')

    if output is None:
        output = 'ontology.owl'
    logging.debug(f'Output ontology is {output}')

    try:
        ontology = compiler.__build(ifiles, namespace, targets)
        ontology.save(output, ontology_format=ontology_format)
        return 0
    except Exception as e:
        logging.error(f'Cannot build ontology: {e}')
        return 2


if __name__ == "__main__":
    sys.exit(__main_cli(sys.argv[1:]))
