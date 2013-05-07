from descriptors import *
from variantfileparser import VarFile

class RefPos( GreaterThanZeroInt ):
    ''' Allow a question mark as a valid input '''
    def __set__( self, inst, value ):
        if value == '?':
            setattr( inst, self.store_name, value )
        else:
            super( RefPos, self ).__set__( inst, value )

class DevLength( GreaterThanZeroInt ):
    ''' Allow a hyphen mark as a valid input '''
    def __set__( self, inst, value ):
        if value == '-':
            setattr( inst, self.store_name, value )
        else:
            super( DevLength, self ).__set__( inst, value )

class StructVars( VarFile ):
    def parse_header( self ):
        super( StructVars, self ).parse_header()
        self.headers = self.headers + ['Var ID']

    def parse_variants( self ):
        for varlines in self.read_until_next_variant():
            sl = self.parse_summary_line( varlines[0] )
            sl['lines'] = varlines[1:]
            refaccno = sl['Ref Accno1']
            self.add_variant( refaccno, StructVariant( **sl ) )

class StructVariant( object ):
    ''' Represents an instance of a variant in the StructVariants '''
    refaccno1 = ""
    refpos1 = GreaterThanZeroInt( 'refpos1' )
    varside1 = ValidSetDescriptor( 'varside1', valid_values=('-->','<--') )
    regionname1 = ""
    refaccno2 = ""
    refpos2 = RefPos( 'refpos2' )
    varside2 = ValidSetDescriptor( 'varside2', valid_values=('-->','<--','?') )
    regionname2 = ""
    totaldepth = GreaterThanZeroInt( 'totaldepth' )
    varfreq = GreaterThanZeroFloat( 'varfreq' )
    deviationlength = DevLength( 'deviationlength' )
    type = ValidSetDescriptor( 'type', valid_values=('Point','Region') )
    fwdwvar = None
    refwvar = None
    fwdtotal = None
    revtotal = None
    varid = ""
    def __init__( self, *args, **kwargs ):
        '''
            Accepts all arguments that are headers that coorespond to a summary line as well as lines which
            should be a list of lines from the summary line down to the ------------------- line
        '''
        self.refaccno1 = kwargs['Ref Accno1']
        self.refpos1 = kwargs['Ref Pos1']
        self.varside1 = kwargs['Var Side1']
        self.regionname1 = kwargs['Region Name1']
        self.refaccno2 = kwargs['Ref Accno2']
        self.refpos2 = kwargs['Ref Pos2']
        self.varside2 = kwargs['Var Side2']
        self.regionname2 = kwargs['Region Name2']
        self.totaldepth = kwargs['Total Depth']
        self.varfreq = kwargs['Var Freq']
        self.deviationlength = kwargs['Deviation Length']
        self.type = kwargs['Type']
        self.varid = kwargs['Var ID']

        if 'fwdwvar' in kwargs:
            self.fwdwvar = kwargs['Fwd w Var']
            self.refwvar = kwargs['Ref w Var']
            self.fwdtotal = kwargs['Fwd Total']
            self.revtotal = kwargs['Rev Total']

        self.lines = kwargs['lines']

    def __str__( self ):
        return "Ref:{refaccno1}\tPos:({_refpos1},{_refpos2})\tTotal Depth:{_totaldepth}\tVar Freq:{_varfreq}\tDeviationLength:{_deviationlength}".format( **self.__dict__ )
