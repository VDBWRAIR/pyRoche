import subprocess
import logging
import argparse
import os
import tempfile

logger = logging.getLogger( __name__ )

class NewblerCommand( object ):
    '''
        Base class to extend for various newbler commands
        Wraps around the command and support running it and detecting
            the status of the command
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
        
            @param exe - Path to an executable for this command
            @raises ValueError if path is not executable or does not exist
        '''
        if not os.path.isfile( exe ):
            raise ValueError( "{} does not exist or is not a file" )
        elif not os.access( exe, os.X_OK ):
            raise ValueError( "{} is not executable" )

        # Set the exe
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
                if argval is not False:
                    args.append( a.option_strings[0] )
            except IndexError:
                pass
            if argval is not True:
                args.append( getattr( namespace, a.dest ) )
        return args

    def add_argument( self, *args, **kwargs ):
        '''
            Wrapper around ArgumentParser.add_argument

            Just stores the _store_action for each added argument to keep track
             of the order in which they were added. Newbler commands are very picky
             about the order sometimes
        
            @param args - List of args for ArgumentParser.add_argument
            @param args - List of kwargs for ArgumentParser.add_argument
        '''
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
        cmd = [self.executable] + self.parse_args( args )
        logger.info( "Running command: {}".format(cmd) )
        stderr = tempfile.SpooledTemporaryFile()
        stdout = subprocess.check_output( cmd, stderr=stderr )
        stderr.seek(0)
        return self.check_output( stdout, stderr.read() )

class AddRun( NewblerCommand ):
    pass
