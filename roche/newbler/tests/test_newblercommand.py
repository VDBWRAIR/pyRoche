from nose.tools import eq_, raises

from .. import newblercommand
import fixtures

import tempfile
import os
from os.path import basename, dirname, splitext, join
import sys
from glob import glob
import shutil
import stat
from contextlib import contextmanager
import subprocess
import argparse

class CommandBase( object ):
    @classmethod
    def setUpClass( self ):
        pass

    @contextmanager
    def tempdir( self ):
        ''' Quick clean up tempdir '''
        tdir = tempfile.mkdtemp()
        yield tdir
        shutil.rmtree( tdir )

    @contextmanager
    def tempfile( self ):
        fd, tfile = tempfile.mkstemp()
        yield tfile
        os.unlink( tfile )

    @contextmanager
    def create_project( self, type='mapping' ):
        '''
            Just creates a newbler project in a temporary directory
             that is deleted after it is used
        
            @param type - Mapping/mapping/map or Assembly/assembly
            
            @returns absolute path to created project inside a temporary directory
        '''
        with self.tempdir() as td:
            os.chdir( td )
            type = type.lower()
            if type in ('map','mapping'):
                cmd = ['newMapping']
            elif type == 'assembly':
                cmd = ['newAssembly']
            print subprocess.check_output( cmd )
            yield join( td, os.listdir( '.' )[0] )

class TestNewMapping( CommandBase ):
    def setUp( self ):
        self.nm = newblercommand.NewMapping()

    def test_checkoutput_newproj( self ):
        # Check that check_output works for this command
        with self.tempdir() as td:
            os.chdir( td )
            self.nm.run( 'testproj' )
            self.nm.run( '-force testproj' )

    @raises( subprocess.CalledProcessError )
    def test_checkoutput_error( self ):
        with self.tempdir() as td:
            os.chdir( td )
            self.nm.run( '-badarg testproj' )

class TestNewAssembly( CommandBase ):
    def setUp( self ):
        self.na = newblercommand.NewAssembly()

    def test_checkoutput_newproj( self ):
        with self.tempdir() as td:
            os.chdir( td )
            self.na.run( 'testproj' )
            self.na.run( '-force testproj' )

    @raises( subprocess.CalledProcessError )
    def test_checkoutput_error( self ):
        with self.tempdir() as td:
            os.chdir( td )
            self.na.run( '-badarg testproj' )

class CreateProjectTestClass( newblercommand.CreateProject ):
    def set_args( self ):
        pass

class TestCreateProject( CommandBase ):
    def setUp( self ):
        self.cp = CreateProjectTestClass(
            'test', ''
        )

    def test_checkoutput_valid( self ):
        output = '{} {} project directory {}'
        tests = (
            ('Created','mapping','testproj1'),
            ('Initialized','mapping','testproj2'),
            ('Created','assembly','testproj3'),
            ('Initialized','assembly','testproj4'),
        )
        for test in tests:
            with self.tempdir() as td:
                os.chdir( td )
                o = output.format(*test)
                print o
                ro = self.cp.check_output(
                    ['test',test[2]],
                    o,
                    ''
                )
                eq_( o, ro )

    @raises(subprocess.CalledProcessError)
    def test_checkoutput_error( self ):
        output = '''Error:  Invalid option: -bob.
Usage:  newMapping/newAssembly [projectDirectory]

These two commands create a new mapping or assembly project, and initialize
the project files/sub-directories.  If the directory does not exist, it will
be created.  If no directory is given on the command line, a new directory
named "P_date_time_runMapping" or "P_date_time_runAssembly" (where "date"
and "time" are the current date and time) will be created in the current
working directory.'''
        self.cp.check_output( ['test','proj'], output, '' )
    
    @raises(subprocess.CalledProcessError)
    def test_checkoutput_usage( self ):
        output = '''Usage:  newMapping/newAssembly [projectDirectory]

These two commands create a new mapping or assembly project, and initialize
the project files/sub-directories.  If the directory does not exist, it will
be created.  If no directory is given on the command line, a new directory
named "P_date_time_runMapping" or "P_date_time_runAssembly" (where "date"
and "time" are the current date and time) will be created in the current
working directory.


(The full documentation for "createProject" command can be found in the user manual).'''
        self.cp.check_output( ['test','proj'], output, '' )

class TestSetRef( CommandBase ):
    def setUp( self ):
        self.sr = newblercommand.SetRef()
        self.files = fixtures.files_for_fixture(
            fixtures.mapping_fixtures[1]
        )
        self.refs = [
            join( 
                fixtures.mapping_fixtures[1],
                'refs',
                ref
            )
            for ref in self.files['refs']
        ]
        self.ref = self.refs[0]
        self.refdir = join(
            fixtures.mapping_fixtures[1],
            'refs'
        )
        self.refs_str = "\n    ".join(
                [basename(ref) for ref in self.refs]
            )

    def test_singlerefvalid( self ):
        with self.create_project() as p:
            output = self.sr.run( "{} {}".format(
                p, self.ref
            ))
            eq_(
                '1 reference files successfully added.\n    {}\n'.format(
                    basename(self.ref)
                ),
                output
            )

    def test_multiplerefvalid( self ):
        with self.create_project() as p:
            output = self.sr.run( "{} {}".format( p, " ".join(self.refs) ) )
            eq_(
                str(len(self.refs)) + \
                    ' reference files successfully added.\n    ' + \
                    self.refs_str + '\n',
                output
            )

    def test_refdirectory( self ):
        with self.create_project() as p:
            output = self.sr.run( "{} {}".format(
                p, self.refdir
            ))
            eq_(
                str(len(self.refs)) + \
                    ' reference files successfully added.\n    ' + \
                    self.refs_str + '\n',
                output
            )

    @raises(subprocess.CalledProcessError)
    def test_missingprojdir( self ):
        self.sr.run( "{}".format(
            self.ref
        ))

    @raises(subprocess.CalledProcessError)
    def test_missingreadfile( self ):
        with self.create_project() as p:
            self.sr.run( "{}".format( p ) )

    @raises(subprocess.CalledProcessError)
    def test_invalidprojdir( self ):
        self.sr.run( "{} {}".format(
            'dne', self.ref
        ))

class TestAddRun( CommandBase ):
    def setUp( self ):
        self.ar = newblercommand.AddRun()
        # Just grab first fixture's files for this
        self.files = fixtures.files_for_fixture(
            fixtures.mapping_fixtures[0]
        )
        self.sffs = [
            join( 
                fixtures.mapping_fixtures[0],
                'sff',
                sff
            )
            for sff in self.files['sff']
        ]
        self.sff = self.sffs[0]

    def test_singlesffvalid( self ):
        with self.create_project() as p:
            output = self.ar.run( '{} {}'.format( p, self.sff ) )
            eq_(
                '1 read file successfully added.\n    454Reads1.sff\n',
                output
            )

    def test_multiplesffvalid( self ):
        with self.create_project() as p:
            output = self.ar.run( '{} {}'.format( p, " ".join(self.sffs) ) )
            eq_(
                '2 read files successfully added.\n    454Reads1.sff\n    454Reads2.sff\n',
                output
            )

    @raises(subprocess.CalledProcessError)
    def test_missingprojdir( self ):
        with self.create_project() as p:
            self.ar.run( '{}'.format( self.sff ) )

    @raises(subprocess.CalledProcessError)
    def test_missingreadfile( self ):
        with self.create_project() as p:
            self.ar.run( '{}'.format( p ) )

    @raises(subprocess.CalledProcessError)
    def test_invalidread( self ):
        with self.create_project() as p:
            self.ar.run( '{} {}'.format( p, 'dne' ) )

    @raises(subprocess.CalledProcessError)
    def test_invalidprojdir( self ):
        with self.create_project() as p:
            self.ar.run( '{} {}'.format( 'dne', self.sff ) )

    @raises(subprocess.CalledProcessError)
    def test_usage( self ):
        with self.create_project() as p:
            self.ar.run( )

    @raises(subprocess.CalledProcessError)
    def test_invalidproj_validsff( self ):
        self.ar.check_output(
            cmd=['test'],
            stdout= '',
            stderr= '''Error:  Neither the first argument nor the current working directory is a project directory.
Usage:  addRun [options] [projectDir] [MID_List@](sfffile | fnafile | [regions:]analysisDirectory)...
Options:
   -p             - These runs/files contain 454 paired reads
   -lib libname   - Default paired-end library to use for these files
   -mcf filename  - Location of multiplex config file


The project directory may either be specified on the command line, or
the program will check the current working directory to see if it is
a project directory (or the mapping/assembly sub-directory), and use it
if so.'''
            )

    def test_checkoutput_output( self ):
        eq_( 
            '1 read file successfully added.\n    somefile.sff\n',
            self.ar.check_output(
                cmd=['addRun','projdir','somefile.sff'],
                stdout='1 read file successfully added.\n    somefile.sff\n',
                stderr=''
            )
        )

    @raises(subprocess.CalledProcessError)
    def test_checkoutput_ensurecorrect( self ):
        self.ar.check_output(
            cmd=['addRun','projdir','sff1.sff','sff2.sff'],
            stdout='1 read file successfully added.\n    sff1.sff\n',
            stderr=''
        )

class FakeNS( object ):
    ''' Fake Namespace object '''
    pass

class NewblerCommandCheckOutput( newblercommand.NewblerCommand ):
    ''' Just implement simple check_output '''
    def __init__( self, *args, **kwargs ):
        super( NewblerCommandCheckOutput, self ).__init__(
            description='Test Command',
            exepath='test'
        )
    def check_output( self, cmd, stdout, stderr ):
        return "O:{}--E:{}".format(stdout,stderr)

    def set_args( self ):
        pass

class TestNewblerCommand( CommandBase ):
    def setUp( self ):
        self.nc = NewblerCommandCheckOutput( )
        self.readfiles = ['my.sff','my.fastq','my.fa','my.fasta','my.fna']
        self.basecmd = ['command','arg1','arg2']


    def test_expectedfiles_single( self ):
        for readfile in self.readfiles:
            # Test each file separately
            eq_(
                [readfile],
                self.nc.expected_files(
                    self.basecmd + [readfile]
                )
            )
            # Ensure abs path works too
            eq_(
                [readfile],
                self.nc.expected_files(
                    self.basecmd + ['/some/path/'+readfile]
                )
            )

    def test_expectedfiles_multiple( self ):
        eq_(
            self.readfiles,
            self.nc.expected_files(
                self.basecmd + [" ".join(self.readfiles)]
            )
        )

    def test_expectedfiles_nonread( self ):
        self.basecmd + ['notaread']
        eq_(
            [],
            self.nc.expected_files(
                self.basecmd
            )
        )

    def test_expectedfiles_dir( self ):
        files = fixtures.files_for_fixture(
            fixtures.mapping_fixtures[1]
        )
        refs = [
            join( 
                fixtures.mapping_fixtures[1],
                'refs',
                ref
            )
            for ref in files['refs']
        ]
        ref = refs[0]
        refdir = join(
            fixtures.mapping_fixtures[1],
            'refs'
        )
        refs_str = "\n    ".join(
                [basename(ref) for ref in refs]
            )
        cmd = self.basecmd + [refdir]
        eq_(
            files['refs'],
            self.nc.expected_files( cmd )
        )
    
    def test_foundfiles_single( self ):
        outputs = [
            ('1 read file successfully added.\n    {}\n','454Reads.sff'),
            ('1 reference files successfully added.\n    {}\n','ref.fna')
        ]
        for output in outputs:
            eq_(
                [output[1]],
                self.nc.found_files( output[0].format(output[1]) )
            )

    def test_foundfiles_multiple( self ):
        outputs = [
            (
                '2 read files successfully added.\n    ',
                ['454Reads1.sff','454Reads2.sff']
            ),
            (
                '2 reference files successfully added.\n    ',
                ['ref1.fna','ref2.fna']
            )
        ]
        for output in outputs:
            o = output[0] + "\n    ".join(output[1]) + '\n'
            eq_(
                output[1],
                self.nc.found_files( o )
            )

    @raises(ValueError)
    def test_foundfiles_erroutput( self ):
        self.nc.found_files(
            'Error:  Reference file/directory does not exist:  bob'
        )

    @raises(ValueError)
    def test_foundfiles_usageoutput( self ):
        self.nc.found_files( '''Usage:  setRef [projectDir] [fastafile | directory | genomename]...
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
results will be removed).''' )


    def test_setvalidexecutable( self ):
        with self.tempfile() as exe:
            os.chmod( exe, stat.S_IXUSR )
            self.nc.executable = exe
            eq_( exe, self.nc.executable )

    @raises(ValueError)
    def test_setexecutablenoexec( self ):
        with self.tempfile() as exe:
            self.nc.executable = exe
            eq_( '', self.nc.executable )

    @raises(ValueError)
    def test_setexecutablenotexist( self ):
        self.nc.executable = 'missing'
        eq_( '', self.nc.executable )

    def test_setexecutable_path( self ):
        # This should not raise an exception
        self.nc.executable = 'find'

    def test_parsevalidargs( self ):
        self.nc.add_argument( '-t1' )
        self.nc.add_argument( '-t2', action='store_true' )
        self.nc.add_argument( dest='testarg2' )
        args = self.nc.parse_args( '-t1 test1 -t2 test3' )
        eq_( '-t1 test1 -t2 test3'.split(), args )

    @raises(SystemExit)
    def test_invalidargs( self ):
        self.nc.parser.add_argument( dest='testarg' )
        args = self.nc.parse_args( [] )

    def test_addargumentvalid( self ):
        self.nc.add_argument( '-t1', dest='testone' )
        self.nc.add_argument( '-a' )
        self.nc.add_argument( dest='last' )
        expected = ['-t1','-a']
        found = [a.option_strings[0] for a in self.nc.args
                    if len(a.option_strings)]
        eq_( expected, found )

    def test_addargumenttomegroup( self ):
        ''' Adding argument to Mutually Exclusive Group '''
        meg = self.nc.parser.add_mutually_exclusive_group()
        self.nc.add_argument( '-t1' )
        self.nc.add_argument( '-me1', group=meg )
        self.nc.add_argument( '-me2', group=meg )
        sysv = '-t1 t1 -me1 me1'
        args = self.nc.parse_args( sysv )
        eq_( sysv.split(), args )

    def test_addargumenttomgroup( self ):
        ''' Adding argument to Mutually Exclusive Group '''
        agroup = self.nc.parser.add_argument_group()
        self.nc.add_argument( '-t1' )
        self.nc.add_argument( '-me1', group=agroup )
        self.nc.add_argument( '-me2', group=agroup )
        sysv = '-t1 t1 -me1 me1'
        args = self.nc.parse_args( sysv )
        eq_( sysv.split(), args )

    def test_getargumentsinorder( self ):
        self.nc.add_argument( '-t1', dest='testone' )
        self.nc.add_argument( '-a' )
        self.nc.add_argument( '-on', action='store_true' )
        self.nc.add_argument( dest='last' )
        ns = FakeNS()
        ns.testone = 'test1'
        ns.a = 'test2'
        ns.on = True
        ns.last = 'test3'
        expected = ['-t1','test1','-a','test2','-on','test3']
        eq_( expected, self.nc.get_arguments_inorder( ns ) )

    def test_getargumentsinorder_removeoptional( self ):
        self.nc.add_argument( '-t1', dest='testone' )
        self.nc.add_argument( '-a' )
        self.nc.add_argument( '-on', action='store_true' )
        self.nc.add_argument( dest='last' )
        ns = FakeNS()
        ns.testone = 'test1'
        ns.a = None
        ns.on = True
        ns.last = 'test3'
        expected = ['-t1','test1','-on','test3']
        eq_( expected, self.nc.get_arguments_inorder( ns ) )

    def test_runargwithspace( self ):
        with self.tempdir() as tdir:
            exe = join( tdir, 'testexe' )
            with open( exe, 'w' ) as fh:
                fh.write( "#!/bin/bash\necho 0" )
            os.chmod( exe, stat.S_IRWXU )
            nc = NewblerCommandCheckOutput( 'test' )
            nc.add_argument(
                dest='args',
                action=newblercommand.ConcatStrAction,
                nargs='+'
            )
            nc.executable = exe
            output = nc.run( 'arg1 arg2' )

    def test_runvalidcommand( self ):
        with self.tempdir() as tdir:
            os.chdir(tdir)
            exe = join( tdir, 'testexe' )
            with open( exe, 'w' ) as fh:
                fh.write( '#!/bin/bash\necho 1\necho 1 1>&2' )
            os.chmod( exe, stat.S_IRWXU )
            nc = NewblerCommandCheckOutput('test')
            nc.executable = exe
            output = nc.run()
            eq_( 'O:1\n--E:1\n', output )

    @raises(subprocess.CalledProcessError)
    def test_runcommand_invalidargs( self ):
        with self.tempdir() as tdir:
            exe = join( tdir, 'testexe' )
            with open( exe, 'w' ) as fh:
                fh.write( "#!/bin/bash\nexit 0" )
            os.chmod( exe, stat.S_IRWXU )
            self.nc.executable = exe
            self.nc.run( 'invalid args' )

    @raises(subprocess.CalledProcessError)
    def test_runcommandnonzero( self ):
        with self.tempdir() as tdir:
            exe = join( tdir, 'testexe' )
            with open( exe, 'w' ) as fh:
                fh.write( "#!/bin/bash\nexit 1" )
            os.chmod( exe, stat.S_IRWXU )
            self.nc.executable = exe
            self.nc.run()

class TestConcatStrAction( object ):
    def setUp( self ):
        self.parser = argparse.ArgumentParser()
        
    def test_singleitemlist( self ):
        self.parser.add_argument(
            dest='testarg',
            action=newblercommand.ConcatStrAction,
            nargs='+'
        )
        args = 'one'
        eq_( args, self.parser.parse_args( args.split() ).testarg )

    def test_multiitemlist( self ):
        self.parser.add_argument(
            dest='testarg',
            action=newblercommand.ConcatStrAction,
            nargs='+'
        )
        args = 'one two three'
        eq_( args, self.parser.parse_args( args.split() ).testarg )

    def test_nonstringitems( self ):
        self.parser.add_argument(
            '--strings',
            dest='concatstr',
            action=newblercommand.ConcatStrAction,
            nargs='+'
        )
        self.parser.add_argument(
            '--ints',
            dest='concatstr',
            action=newblercommand.ConcatStrAction,
            nargs='+'
        )
        args = '--strings one two three --ints 1 2 3'
        eq_(
            'one two three 1 2 3',
            self.parser.parse_args( args.split() ).concatstr
        )
