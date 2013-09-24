import subprocess
import logging
import argparse
import os
import tempfile
import re
from os.path import basename

import util

logger = logging.getLogger( __name__ )

class NewblerCommand( object ):
    '''
        Base class to extend for various newbler commands
        Wraps around the command and support running it and detecting
            the status of the command

        Subclasses need to do the following:
            Set self.executable to Path/Name of executable
            Define self.set_args by setting all of the arguments(ArgumentParser objects)
            Define self.check_output by defining how to parse the stdout & stderr of the
                command that will be ran to check for errors. Not all commands simply
                return 1 on an error which will raise a subprocess.CalledProcessError
    '''
    def __init__( self, description ):
        # The argument parser object
        self.parser = argparse.ArgumentParser( description=description )
        # The executable to run
        self._executable = ''
        # Arguments added in order will be kept here
        self.args = []

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

    def check_output( self, stdout=None, stderr=None ):
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

    def run( self, args='' ):
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
            raise subprocess.CalledProcessError(
                cmd = self.executable + ' ' + args,
                returncode = 1,
                output = e.message
            )
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

class AddRun( NewblerCommand ):
    def __init__( self, *args, **kwargs ):
        '''
            @param exepath - Optional path to executable for addRun[Default is just addRun]
        '''
        super( AddRun, self ).__init__( "Command to add Read Data to an existing project" )
        if 'exepath' in kwargs:
            self.executable = kwargs['exepath']
        else:
            self.executable = 'addRun'

        self.set_args()

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
        self.add_argument(
            dest='projDir',
            help='Project Directory to add runs too'
        )
        self.add_argument(
            dest='filedesc',
            action=ConcatStrAction,
            nargs='+',
            help='You can read about filedesc in the Roche Software Manual'
        )

    def check_output( self, cmd, stdout=None, stderr=None ):
        # Flag to tell if errors were detected in output
        err = False
        if stderr.startswith( 'Error:' ):
            err = True
        else:
            outlines = stdout.splitlines()
            readargs = [readfile for readfile in cmd \
                 if '.sff' in readfile or '.fastq' in readfile or '.fna' in readfile]
            readfiles = [basename(read) for readarg in readargs \
                                for read in readarg.split()]
            logger.debug( "Expecting addRun to add {}".format(",".join(readfiles)) )
            foundreadfiles = []
            if not re.match( '\d read file[s]* successfully added.', outlines[0] ):
                logger.warning( "addRun did not successfully add reads" )
                err = True
            for addedread in outlines[1:]:
                m = re.match( '    (.*)', addedread )
                if not m:
                    err = True
                    logger.warning( "output from addRun did not indicate that it added a read: {}".format(
                        addedread
                    ))
                    break
                else:
                    foundreadfiles.append( m.group(1) )
            foundreadfiles.sort()
            if foundreadfiles != readfiles:
                logger.warning( "Expecting reads {} to be added but only added {}".format(
                    ",".join(readfiles), ",".join(foundreadfiles)
                ))
                err = True

        if err:
            raise subprocess.CalledProcessError(
                cmd = cmd,
                returncode = 0,
                output = stdout + stderr
            )
        else:
            logger.info( "Sucessfully added reads to project" )
            return stdout

class SetRef(NewblerCommand):
    def __init__( self, *args, **kwargs ):
        '''
            @param exepath - Optional path to executable for addRun[Default is just addRun]
        '''
        super( AddRun, self ).__init__( "Command to add references to an existing project" )
        if 'exepath' in kwargs:
            self.executable = kwargs['exepath']
        else:
            self.executable = 'setRef'

        self.set_args()

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
        self.add_argument(
            dest='projDir',
            help='Project path to set references for'
        )
        self.add_argument(
            dest='refereces',
            action=ConcatStrAction,
            nargs='+',
            help='Directory or fastafile'
        )

    def check_output( self, cmd, stdout=None, stderr=None ):
        pass
