from nose.tools import eq_, raises

from .. import newblercommand

import tempfile
import os
from os.path import basename, dirname, splitext, join
import sys
from glob import glob
import shutil
import stat
from contextlib import contextmanager
import subprocess

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

class FakeNS( object ):
    pass

class NewblerCommandCheckOutput( newblercommand.NewblerCommand ):
    ''' Just implement simple check_output '''
    def check_output( self, stdout, stderr ):
        return "O:{}--E:{}".format(stdout,stderr)

    def set_args( self ):
        pass

class TestNewblerCommand( CommandBase ):
    def setUp( self ):
        self.nc = newblercommand.NewblerCommand( "Test Command" )

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
        eq_( sysv.split() + ['-me2',None], args )

    def test_addargumenttomgroup( self ):
        ''' Adding argument to Mutually Exclusive Group '''
        agroup = self.nc.parser.add_argument_group()
        self.nc.add_argument( '-t1' )
        self.nc.add_argument( '-me1', group=agroup )
        self.nc.add_argument( '-me2', group=agroup )
        sysv = '-t1 t1 -me1 me1'
        args = self.nc.parse_args( sysv )
        eq_( sysv.split() + ['-me2',None], args )

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

    def test_runvalidcommand( self ):
        with self.tempdir() as tdir:
            exe = join( tdir, 'testexe' )
            with open( exe, 'w' ) as fh:
                fh.write( '#!/bin/bash\necho 1\necho 1 1>&2' )
            os.chmod( exe, stat.S_IRWXU )
            nc = NewblerCommandCheckOutput('test')
            nc.executable = exe
            output = nc.run()
            eq_( 'O:1\n--E:1\n', output )

    @raises(subprocess.CalledProcessError)
    def test_runcommandnonzero( self ):
        with self.tempdir() as tdir:
            exe = join( tdir, 'testexe' )
            with open( exe, 'w' ) as fh:
                fh.write( "#!/bin/bash\nexit 1" )
            os.chmod( exe, stat.S_IRWXU )
            self.nc.executable = exe
            self.nc.run()
