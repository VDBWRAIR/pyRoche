from os.path import join, basename, dirname, splitext

from nose.tools import eq_, raises

from ..util import *
from .. import util
import fixtures

class TestRefFileForIdent( fixtures.FixtureMapBase ):
    def test_fullidentname( self ):
        ''' Ensure full identifier name works '''
        for mproj,fix in self.mprojs:
            fixrefs = fixtures.refs_for_fixture( fix )
            ref, idents = fixrefs.items()[0]
            ref = join(fix,'refs',ref)

            rf = reference_file_for_identifier( idents[0], mproj )
            eq_( ref, rf )

    def test_partialidentname( self ):
        for mproj,fix in self.mprojs:
            fixrefs = fixtures.refs_for_fixture( fix )
            ref, idents = fixrefs.items()[0]
            ref = join(fix,'refs',ref)

            # Ensure partial identifier name works
            rf = reference_file_for_identifier( idents[0][0:10], mproj )
            eq_( ref, rf )

    def test_notfound( self ):
        ''' Make sure none is returned when no ref file is found '''
        for mproj,fix in self.mprojs:
            fixrefs = fixtures.refs_for_fixture( fix )
            ref, idents = fixrefs.items()[0]
            ref = join(fix,'refs',ref)

            # Ensure partial identifier name works
            rf = reference_file_for_identifier( 'doesnotexist', mproj )
            eq_( None, rf )

class TestFindInPath( object ):
    def test_find_valid( self ):
        # I think find is on windows too?
        assert util.find_in_path( 'find' ) is not None

    def test_find_missing( self ):
        assert util.find_in_path( 'sskkyi' ) is None
