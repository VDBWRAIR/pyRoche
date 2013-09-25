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
            return self.check_output( cmd, stdout, stderr.read() )
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
