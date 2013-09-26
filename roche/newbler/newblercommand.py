import subprocess
import logging
import argparse
import os
import tempfile
import re
from os.path import basename,splitext
import sys

import util

logger = logging.getLogger( __name__ )

class NewblerCommand( object ):
    '''
        Base class to extend for various newbler commands
        Wraps around the command and support running it and detecting
            the status of the command

        Subclasses need to do the following:
            Define __init__ and call super and pass the description and exepath to
                the constructor.
            Define set_args by setting all of the arguments(ArgumentParser objects)
            Define check_output by defining how to parse the stdout & stderr of the
                command that will be ran to check for errors. Not all commands simply
                return 1 on an error which will raise a subprocess.CalledProcessError
    '''
    def __init__( self, description, exepath=None ):
        '''
            Sets up the argument parser instance and executable

            @param description - The description of the command that is being wrapped
            @param exepath - The path to the executable
        '''
        # The argument parser object
        self.parser = argparse.ArgumentParser( description=description )
        # The executable to run
        self._executable = ''
        # Arguments added in order will be kept here
        self.args = []

        if exepath is not None:
            self.executable = exepath

        # Set Up the args
        self.set_args()

    def expected_files( self, cmd ): 
        '''
            Parses a command list into expected files. Useful for parsing addRun and setRef output.
            Detects the following file formats:
                .fasta
                .fna
                .sff
                .fastq
                .fa

            Typically the reads are in a single huge string because of the use of the ConcatStrAction
             when parsing the arguments.

            @param cmd - List of command parameters from parse_args

            @returns a list of expected files that should be found in output
        '''
        valid_extensions = ('.sff','.fasta','.fastq','.fna','.fa')
        files = []
        # If the last argument is a directory
        if os.path.isdir( cmd[-1] ):
            return os.listdir( cmd[-1] )

        # Otherwise parse all the cmds and pull out the reads
        for arg in cmd:
            foundext = False
            for ext in valid_extensions:
                if ext in arg:
                    foundext = True
            if foundext:
                files += [basename(f) for f in arg.split()]
        return files

    def found_files( self, output ):
        '''
            Parses command output to get a list of all the files that were added by the command.
            Useful for parsing addRun and setRef output

            @param output - A string of output. Probably stdout from setRef or addRun.
            @raises ValueError if usage or error output is given or no reads can be parsed out

            @returns a list of files that were listed in the output

            Note: It this does not check that the read files that were added are valid read files.
                It is assumed that all added files by newbler commands are valid
        '''
        patt = '(\d+) \w+ file[s]* successfully added.\n((^    .*?\n)+)'
        m = re.search( patt, output, re.M )
        if not m:
            logger.debug( "Could not parse {} into found files".format(output) )
            raise ValueError( "Output does indicate successfully adding any files" )

        numfiles = m.group( 1 )
        files = m.group( 2 ).split()
        # Check to see if newbler command gives incorrect amount of files it added
        if int( numfiles ) != len( files ):
            # I'm not sure that this could even happen, but why not be safe
            logger.critical( "Output indicates that {} files should have " \
                "been added but {} were added".format(numfiles,files)
            )
            raise ValueError( "Something very wrong just happened" )

        return files

    @property
    def executable( self ):
        return self._executable

    @executable.setter
    def executable( self, exe ):
        '''
            Sets the executable name after checking to make
            sure it exists and is executable
        
            @param exe - Path to an executable for this command or executable in PATH
            @raises ValueError if path is not executable or does not exist
        '''
        executable = exe
        if not os.path.isfile( exe ):
            # Need to see if it is in the path
            executable = util.find_in_path( exe )

        if executable is None:
            raise ValueError( "{} does not exist or is not a file".format(exe) )
        elif not os.access( executable, os.X_OK ):
            raise ValueError( "{} is not executable".format(exe) )

        # Set the exe to the user supplied value
        self._executable = exe

    def get_arguments_inorder( self, namespace ):
        '''
            Returns arguments in the order that they were added

            @param namespace - Namespace returned from parsing the arguments

            @returns in order list of arguments and their values
        '''
        args = []
        for a in self.args:
            argval = getattr( namespace, a.dest )
            try:
                # Check to see if argval is None or None value(False, '', []...)
                if argval:
                    args.append( a.option_strings[0] )
            except IndexError:
                # Argument did not have named option
                #  so only add argval below
                pass
            # Don't put True values or values that are none types
            if argval is not True and argval:
                args.append( getattr( namespace, a.dest ) )
        return args

    def add_argument( self, *args, **kwargs ):
        '''
            Wrapper around ArgumentParser.add_argument

            Just stores the _store_action for each added argument to keep track
             of the order in which they were added. Newbler commands are very picky
             about the order sometimes
            Supports adding to groups(arg group & Mutually Exclusive) as well by supplying the group option
        
            @param args - List of args for ArgumentParser.add_argument
            @param kwargs - List of kwargs for ArgumentParser.add_argument
            @param group - Mutually exclusive group to add the argument too
        '''
        if 'group' in kwargs:
            group = kwargs['group']
            del kwargs['group']
            sa = group.add_argument( *args , **kwargs )
        else:
            sa = self.parser.add_argument( *args, **kwargs )
        self.args.append( sa )

    def set_args( self ):
        '''
            Set up the arguments for the command

            Should add arguments to self.parser using self.add_argument
        '''
        raise NotImplementedError( "Needs to be implemented in a subclass" )

    def projdir_arg( self ):
        '''
            Convienience function to simply add project directory arg
            It is a bit goofy that Roche decided that projDir could be an optional
            argument considering it is a positional argument.
            For now in pyRoche projDir is required no matter what
        '''
        self.add_argument(
            dest='projDir',
            help='Project directory'
        )

    def parse_args( self, args ):
        '''
            Runs self.parser.parse_args()

            @param args - String or list of arguments to be parsed

            @returns argument list as a list in the same order that arguments are added to parser
                or raises one of the argparse errors if the arguments were not correct
        '''
        if isinstance( args, str ):
            args = args.split()
        ns = self.parser.parse_args( args )
        return self.get_arguments_inorder( ns )

    def check_output( self, cmd, stdout=None, stderr=None ):
        '''
            Checks the output of the command after it has been run
            
            Should know the expected outcome and how to detect when the command fails or
                succeeds

            @param cmd - Command that generated the output
            @param stdout - The output from the program or None if no output is generated
            @param stderr - The output from the program's stderr or None if no output is generated
            @returns output if the command was successful or raises subprocess.CalledProcessError
                if there was an error running the command
        '''
        raise NotImplementedError( "Needs to be implemented in a subclass" )

    def run( self, args=" ".join( sys.argv[1:] ) ):
        '''
            Runs the newbler command in a subprocess
            Should more or less simply add the options from self.parse_args onto
             self.executable and call subprocess.Popen on that command

            @param args - List or string of arguments for the command.
            
            @returns the output of the command or by proxy raises a subprocess.CalledProcessError
                if the command failed to run
        '''
        try:
            cmd = [self.executable] + self.parse_args( args )
        except SystemExit as e:
            errormsg = "Incorrect arguments {} given to command {}".format(
                args, self.executable
            )
            logger.warning( errormsg )
            raise subprocess.CalledProcessError(
                cmd = self.executable + ' ' + args,
                returncode = 1,
                output = errormsg
            )

        # flatten the cmd list
        ccmd = []
        for c in cmd:
            if isinstance( c, list ):
                ccmd += c
            else:
                ccmd.append( c )
        cmd = ccmd

        logger.debug( "Args: {}".format( ccmd ) )
        logger.info( "Running command: {}".format(" ".join(cmd)) )
        stderr = tempfile.SpooledTemporaryFile()
        try:
            stdout = subprocess.check_output( cmd, stderr=stderr )
            stderr.seek(0)
            o = self.check_output( cmd, stdout, stderr.read() )
            logger.info( "Successfully ran {}".format(cmd) )
            return o
        except subprocess.CalledProcessError as e:
            stderr.seek(0)
            logger.warning( "{} generated an error STDOUT:{} STDERR:{}".format(
                " ".join( e.cmd ), e.output, stderr.read()
            ) )
            raise e

class ConcatStrAction( argparse.Action ):
    ''' Simply concat the option strings '''
    def __call__( self, parser, namespace, values, option_string=None ):
        val = getattr( namespace, self.dest )
        if not isinstance( val, str ):
            val = ''
        else:
            val += ' '
        val += " ".join( [str(s) for s in values] )
        setattr( namespace, self.dest, val )

class AddFilesBase( NewblerCommand ):
    def check_output( self, cmd, stdout=None, stderr=None ):
        # Flag to tell if errors were detected in output
        err = False
        if stderr.startswith( 'Error:' ):
            err = True
        else:
            expected_files = sorted( self.expected_files( cmd ) )
            try:
                found_files = sorted( self.found_files( stdout ) )
            except ValueError as e:
                err = True

            if found_files != expected_files:
                logger.warning( "Expecting reads {} to be added but added {}".format(
                    ",".join(expected_files), ",".join(found_files)
                ))
                err = True

        if err:
            raise subprocess.CalledProcessError(
                cmd = cmd,
                returncode = 0,
                output = stdout + stderr
            )
        else:
            logger.info( "Sucessfully added files to project" )
            return stdout

class AddRun( AddFilesBase ):
    def __init__( self, *args, **kwargs ):
        '''
            @param exepath - Optional path to executable for addRun[Default is just addRun]
        '''
        super( AddRun, self ).__init__(
            description="Command to add Read Data to an existing project",
            exepath=kwargs.get( 'exepath', 'addRun' )
        )

    def set_args( self ):
        ''' Sets all the ArgumentParser args for this command '''
        pnp = self.parser.add_mutually_exclusive_group()
        mcfc = self.parser.add_mutually_exclusive_group()
        self.add_argument(
            '-p',
            help='Specify that sff file comes from Paired End Sequencing',
            group=pnp
        )
        self.add_argument(
            '-np',
            help='Specify that sff file comes from non-Paired End Sequencing',
            group=pnp
        )
        self.add_argument(
            '-lib',
            help='Define paired end library'
        )
        self.add_argument(
            '-mcf',
            help='Specify non default Mid Config file',
            group=mcfc
        )
        self.add_argument(
            '-custom',
            help='Specify a custom mid group',
            group=mcfc
        )
        self.projdir_arg()
        self.add_argument(
            dest='filedesc',
            nargs='+',
            help='You can read about filedesc in the Roche Software Manual'
        )

class SetRef(AddFilesBase):
    def __init__( self, *args, **kwargs ):
        super( SetRef, self ).__init__(
            description="Command to add references to an existing project",
            exepath=kwargs.get( 'exepath', 'setRef' )
        )

    def set_args( self ):
        '''
            Usage:  setRef [projectDir] [fastafile | directory | genomename]...
            Options:
               -cref   - For cDNA projects, treat the reference as a transcriptome
               -gref   - For cDNA projects, treat the reference as a genome
               -random - For a GoldenPath database, include the *_random.fa
                             and *_hap_*.fa files in what is used as the reference

            This command resets the reference sequence for a mapping project.
            It takes one or more FASTA files, directories (where all of the FASTA
            files in the directories will be used) or GoldenPath genome names (if
            the GOLDENPATH environment variable has been set to the location of
            downloaded GoldenPath genome directory trees.

            Running this command will result in a recomputation of the mapping
            alignments the next time runProject is executed.  (All existing
            results will be removed).


            (The full documentation for "setRef" command can be found in the user manual).
        '''
        gcref = self.parser.add_mutually_exclusive_group()
        self.add_argument(
            '-cref',
            help='For cDNA projects, treat the reference as a genome',
            group=gcref
        )
        self.add_argument(
            '-gref',
            help='For cDNA projects, treat the reference as a transcriptome',
            group=gcref
        )
        self.add_argument(
            '-random',
            help='Used for a GoldenPath database'
        )
        self.projdir_arg()
        self.add_argument(
            dest='references',
            nargs='+',
            help='Directory or fastafile'
        )

class CreateProject(NewblerCommand):
    def set_args( self ):
        self.add_argument(
            '-force',
            action='store_true',
            help='Force overwrite of an already existing project'
        )
        self.add_argument(
            '-cdna',
            action='store_true',
            help='Flag for transcriptome projects'
        )
        self.add_argument(
            '-multi',
            action='store_true',
            help='Flag to specify creation of a multiplex project'
        )

    def check_output( self, cmd, stdout, stderr ):
        validout = '(Created|Initialized) (mapping|assembly) project directory {}'.format(
            cmd[-1]
        )
        if re.match( validout, stdout ):
            return stdout
        else:
            logger.warning( "Output of running {} did not indicate " \
                " that a new project was created".format(
                    " ".join(cmd)
                )
            )
            raise subprocess.CalledProcessError(
                cmd = cmd,
                returncode = 1,
                output = stdout + stderr
            )

class NewMapping(CreateProject):
    def __init__( self, *args, **kwargs ):
        super( NewMapping, self ).__init__(
            description='Initializes a new mapping project',
            exepath=kwargs.get( 'exepath', 'newMapping' )
        )

    def set_args( self ):
        super( NewMapping, self ).set_args()
        cgref = self.parser.add_mutually_exclusive_group()
        self.add_argument(
            '-cref',
            action='store_true',
            help='Flag for cDNA reference sequence',
            group=cgref
        )              
        self.add_argument(
            '-gref',
            action='store_true',
            help='Flag for genomic reference sequence',
            group=cgref
        )
        self.projdir_arg( )

class NewAssembly(CreateProject):
    def __init__( self, *args, **kwargs ):
        super( NewAssembly, self ).__init__(
            description='Initializes a new assembly project',
            exepath=kwargs.get( 'exepath', 'newAssembly' )
        )

    def set_args( self ):
        super( NewAssembly, self ).set_args()
        self.projdir_arg()

class RunProject(NewblerCommand):
    def __init__( self, *args, **kwargs ):
        super( RunProject, self ).__init__(
            description='Runs an already created mapping/assembly project',
            exepath=kwargs.get( 'exepath', 'runProject' )
        )

    def set_args( self ):
        self.add_argument(
            '--version',
            action='store_true',
            help='Display command version'
        )
        self.add_argument(
            '-a',
            help='Flag to specify minimum length of multiple alignments of contigs' \
                ' to include in 454AllContigs.fna.'
        )
        self.add_argument(
            '-accno',
            action='store_true',
            help='Flag to specify an accno renaming file. Mapping Only.'
        )
        self.add_argument(
            '-ace',
            action='store_true',
            help='Flag to specify single ace file generation'
        )
        self.add_argument(
            '-acedir',
            help='Flag to generate ace file subdirectory with an ace file for each contig'
        )
        self.add_argument(
            '-ad',
            action='store_true',
            help='Flag to output default reads in ACE or consed folder'
        )
        self.add_argument(
            '-ads',
            action='store_true',
            help='Flag to set the alignment difference score parameter'
        )
        self.add_argument(
            '-ais',
            action='store_true',
            help='Flag to sed the alignment identity score parameter'
        )
        self.add_argument(
            '-annot',
            help='File with gene-coding/region annotation for ref sequence.' \
                'Mapping only.'
        )
        self.add_argument(
            '-ar',
            action='store_true',
            help='Flag to output full raw read sequences in ace or consed folder'
        )
        self.add_argument(
            '-at',
            action='store_true',
            help='Flag to output only trimmed sequence reads in ace or consed folder'
        )
        self.add_argument(
            '-bam',
            action='store_true',
            help='Flag to generate bam file containing the multiple alignments for the contigs.' \
                ' Mapping only'
        )
        self.add_argument(
            '-bamsub',
            action='store_true',
            help='Flag to specify bam adjacent indel substitution'
        )
        self.add_argument(
            '-batchsize',
            help='Flag to specify the number of sample projects to be computed in parallel'
        )
        self.add_argument(
            '-consed',
            action='store_true',
            help='Flag to generate a consed file subdirectory'
        )
        self.add_argument(
            '-consed16',
            action='store_true',
            help='Flag to generate output compatible with version of consed older than V17.0'
        )
        self.add_argument(
            '-cpu',
            help='How many CPU\'s to use for each project'
        )
        self.add_argument(
            '-d',
            help='Flag to set the minimum contig depth. Mapping Only'
        )
        self.add_argument(
            '-e',
            help='Flag to specify expected depth of data'
        )
        self.add_argument(
            '-fd',
            help='Specify full variant file'
        )
        self.add_argument(
            '-fe',
            help='Exclude filter file'
        )
        self.add_argument(
            '-fi',
            help='Include filter file'
        )
        self.add_argument(
            '-het',
            action='store_true',
            help='Enable heterozygotic mode. Assembly only'
        )
        self.add_argument(
            '-hsl',
            help='Hit-per-seed limit. Mapping only'
        )
        self.add_argument(
            '-icc',
            help='Maximum number of contigs in an isotig. Assembly only'
        )
        self.add_argument(
            '-icl',
            help='Minimum length of contig to be included in isotig. Assembly only'
        )
        self.add_argument(
            '-ig',
            help='Maximum number of contigs in an isogroup. Assembly only'
        )
        self.add_argument(
            '-info',
            action='store_true',
            help='Output 454AlignmentInfo.tsv file'
        )
        self.add_argument(
            '-infoall',
            action='store_true',
            help='Output 454AlignmentInfo.tsv including 0-coverage positions'
        )
        self.add_argument(
            '-isplit',
            action='store_true',
            help='Initiate isotig traversal when depth spikes in alignments are found' \
                'Assembly only'
        )
        self.add_argument(
            '-it',
            help='Maximum number of isotigs in an isogroup. Assembly only'
        )
        self.add_argument(
            '-l',
            help='Minimum length for contig to appear in 454LargeContigs.fna'
        )
        self.add_argument(
            '-large',
            action='store_true',
            help='Enable large genome assembly mode. Assembly only'
        )
        self.add_argument(
            '-m',
            action='store_true',
            help='Keep sequence data in memory to speed up cpu time'
        )
        self.add_argument(
            '-maxsvf',
            help='Control the maximum variant frequency values in variant frequency reports' \
                'Mapping only'
        )
        self.add_argument(
            '-mi',
            help='Minimum overlap identity'
        )
        self.add_argument(
            '-minlen',
            help='Minimum length of paired end reads used in computations'
        )
        self.add_argument(
            '-minsvf',
            help='Minimum variant frequency values in variant frequency reports' \
                'Mapping only'
        )
        self.add_argument(
            '-ml',
            help='Minimum overlap length. Percentage of read length(Put %% ' \
                'immediately after number) or integer'
        )
        self.add_argument(
            '-mrerun',
            help='Re-compute a multiplex project'
        )
        self.add_argument(
            '-notrim',
            action='store_true',
            help='Turn off default quality and primer trimming of reads'
        )
        self.add_argument(
            '-nft',
            action='store_true',
            help='Append a column to 454AlignmentInfo.tsv that reports the' \
                ' counts of bases and gaps'
        )
        self.add_argument(
            '-nimblegen',
            action='store_true',
            help='Specify reads should be primer-trimmed using the early ' \
                'NimbleGen Sequence Capture primer sequence. ' \
                'Mapping only'
        )
        self.add_argument(
            '-no',
            action='store_true',
            help='Specify no output of most files'
        )
        self.add_argument(
            '-noaccno',
            action='store_true',
            help='Deactivate use of an accno renaming file. Mapping only'
        )
        self.add_argument(
            '-noace',
            action='store_true',
            help='No ace file generation'
        )
        self.add_argument(
            '-noannot',
            action='store_true',
            help='Disable automatic reading of annotation file. Mapping only'
        )
        self.add_argument(
            '-nobam',
            action='store_true',
            help='Suppress bam file generation. Mapping only'
        )
        self.add_argument(
            '-nobig',
            action='store_true',
            help='Skip output of large files'
        )
        self.add_argument(
            '-nofe',
            action='store_true',
            help='Disable use of exclude filter file'
        )
        self.add_argument(
            '-nofi',
            action='store_true',
            help='Disable use of include filter file'
        )
        self.add_argument(
            '-nohet',
            action='store_true',
            help='Disable heterozygotic mode. Assembly only'
        )
        self.add_argument(
            '-noinfo',
            action='store_true',
            help='Suppress output of 454AlignmentInfo.tsv'
        )
        self.add_argument(
            '-noisplit',
            help='Do not initiate isotig traversal. Assembly only.'
        )
        self.add_argument(
            '-nolarge',
            action='store_true',
            help='Disable large genome assembly mode. Assembly only'
        )
        self.add_argument(
            '-non',
            '-nonimblegen',
            action='store_true',
            help='Turn off NimbleGen mapping mode. Mapping only'
        )
        self.add_argument(
            '-nop',
            action='store_true',
            help='Turn off generation of 454PairAlign.txt'
        )
        self.add_argument(
            '-nor',
            action='store_true',
            help='Turn off automatic rescore function for read quality scores'
        )
        self.add_argument(
            '-noreg',
            action='store_true',
            help='Turn off sequence region based generation of output. Mapping only'
        )
        self.add_argument(
            '-norip',
            action='store_true',
            help='Turn off output of each read in a single contig. Assembly only'
        )
        self.add_argument(
            '-nosnp',
            action='store_true',
            help='Disable the automatic reading of known SNP files. Mapping only'
        )
        self.add_argument(
            '-nosrv',
            action='store_true',
            help='Disable single read variant output. Mapping only'
        )
        self.add_argument(
            '-nosv',
            action='store_true',
            help='Disable structural variant detection. Mapping only'
        )
        self.add_argument(
            '-novs',
            action='store_true',
            help='Turn off a vector screening database used in earlier part of the computation.'
        )
        self.add_argument(
            '-nov',
            '-novt',
            action='store_true',
            help='Turn off vector trimming database FASTA file.'
        )
        self.add_argument(
            '-numn',
            help='Threshold for number of Ns in a read. Reads with > this will be rejected'
        )
        self.add_argument(
            '-pair',
            help='Output pairwise ovrlaps in txt file'
        )
        self.add_argument(
            '-pt',
            '-pairt',
            help='Output pairwise overlaps in tsv file'
        )
        self.add_argument(
            '-qo',
            action='store_true',
            help='Generate quick output for mapping and assembly'
        )
        self.add_argument(
            '-r',
            action='store_true',
            help='Restart the computation'
        )
        self.add_argument(
            '-reg',
            help='Only output specified sequence retion of reference and aligned reads ' \
                'Mapping only'
        )
        self.add_argument(
            '-rescore',
            action='store_true',
            help='Rescore an SFF file using quality score lookup table'
        )
        self.add_argument(
            '-rip',
            action='store_true',
            help='Output each read in only one contig. Assembly only'
        )
        self.add_argument(
            '-rst',
            help='Set the repeat score threshold. Mapping only'
        )
        self.add_argument(
            '-s',
            help='Minimum scaffold size. Assembly only'
        )
        self.add_argument(
            '-sc',
            help='Seed count'
        )
        self.add_argument(
            '-scaffold',
            action='store_true',
            help='Enable gap-filling when low-quality portions of reads ' \
                'at the endso f scaffolding contigs indicate an overlap ' \
                ' Assembly only'
        )
        self.add_argument(
            '-short',
            action='store_true',
            help='Reads shorter than 50bp are used if paired end data is used'
        )
        self.add_argument(
            '-sio',
            action='store_true',
            help='Use Serial I/O. Use in projects with > 4 million reads'
        )
        self.add_argument(
            '-sl',
            help='Seed length'
        )
        self.add_argument(
            '-snp',
            help='File with known SNP information. Mapping only'
        )
        self.add_argument(
            '-ss',
            help='Seed step'
        )
        self.add_argument(
            '-srv',
            action='store_true',
            help='Single read variant output. Mapping only'
        )
        self.add_argument(
            '-sveg',
            help='Structural variation excluded genes file. Mapping only'
        )
        self.add_argument(
            '-tr',
            action='store_true',
            help='Output 454TrimmedReads.{fna,qual} files'
        )
        self.add_argument(
            '-trim',
            action='store_true',
            help='Turn on default quality and primer trimming of reads'
        )
        self.add_argument(
            '-ud',
            action='store_true',
            help='Treat each read separately with no grouping into duplicates'
        )
        self.add_argument(
            '-urt',
            action='store_true',
            help='Extend contigs using the ends of single reads. Assembly only'
        )
        self.add_argument(
            '-vs',
            help='Vector screening database fasta file. Reads must match exactly ' \
                'to be excluded'
        )
        self.add_argument(
            '-v',
            '-vt',
            help='Vector trimming database fasta file for primers, vectors, adaptors ' \
                'and other end sequences'
        )
        self.projdir_arg()

    def check_output( self, cmd, stdout, stderr ):
        err = False
        if 'Error:' in stdout or 'Error:' in stderr:
            errmsg = 'Detected an error in output:'
            err = True
        else:
            startre = '\w+ computation starting at: \w+ \w+ \d+ \d+:\d+:\d+ \d+  \(v2.8 \(\w+\)\)'
            endre = '\w+ computation succeeded at: \w+ \w+ \d+ \d+:\d+:\d+ \d+'
            stdoutlines = stdout.splitlines()
            if not re.search( startre, stdoutlines[0] ):
                print stdoutlines[0]
                errmsg = 'Did not successfully start the computation:'
                err = True
            elif not re.search( endre, stdoutlines[-1] ):
                print stdoutlines[-1]
                errmsg = 'Computation did not successfully finish:'
                err = True

        if err:
            raise subprocess.CalledProcessError(
                cmd = cmd,
                returncode = 1,
                output = errmsg + '\n' + stdout + stderr
            )
