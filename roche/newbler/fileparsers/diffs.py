from variantfileparser import VarFile, Variant
from descriptors import *

class Diffs( VarFile ):
    ''' 454AllDiffs.txt and 454HCDiffs.txt '''
    def parse_variants( self ):
        for varlines in self.read_until_next_variant():
            sl = self.parse_summary_line( varlines[0] )
            sl['lines'] = varlines[1:]
            key = sl['>Reference >Accno']
            # Remove the stupid > chars 
            sl['Reference Accno'] = key
            self.add_variant( key, DiffVariant( **sl ) )

class DiffVariant( Variant ):
    ''' Hold variant information from 454All/HCDiffs.txt '''
    reference_accno = ""
    start_pos = GreaterThanZeroInt( 'start_pos' )
    end_pos = GreaterThanZeroInt( 'end_pos' )
    ref_nuc = ''
    var_nuc = ''
    total_depth = GreaterThanZeroInt( 'total_depth' )
    var_freq = GreaterThanZeroPercent( 'var_freq' )
    ref_aa = ''
    var_aa = ''
    coding_frame = ValidSetDescriptor( 'coding_frame', valid_values=('-3','-2','-1','+1','+2','+3','+','-') )
    region_name = ""
    known_snps = ""
    near_snps = ""
    fwd_w_var = GreaterThanEqualZeroInt( 'fwd_w_var' )
    rev_w_var = GreaterThanEqualZeroInt( 'rev_w_var' )
    fwd_total = GreaterThanEqualZeroInt( 'fwd_total' )
    rev_total = GreaterThanEqualZeroInt( 'rev_total' )

    tgt_region_status = ValidSetDescriptor( 'tgt_region_status', valid_values=('InRegion','InExtRegion') )
    
    def __init__( self, *args, **kwargs ):
        self.lines = kwargs['lines']
        del kwargs['lines']
        kwargs = self.mapkeys( kwargs )
        always = (
            'reference_accno',
            'start_pos',
            'end_pos',
            'ref_nuc',
            'var_nuc',
            'total_depth',
            'var_freq',
        )
        self.set_attributes( always, kwargs )
        self.parse_fd_options( kwargs )
        self.parse_reg_options( kwargs )

    def parse_fd_options( self, kwargs ):
        ''' If -fd option was used '''
        if 'Ref AA' in kwargs or 'ref_aa' in kwargs:
            fd_options = (
    			'ref_aa',
    			'var_aa',
    			'coding_frame',
    			'region_name',
    			'known_snps',
    			'near_snps',
    			'fwd_w_var',
    			'rev_w_var',
    			'fwd_total',
    			'rev_total',
            )
            self.set_attributes( fd_options, kwargs )

    def parse_reg_options( self, kwargs ):
        ''' If -reg option was used '''
        if 'Tgt Region Status' in kwargs or 'tgt_region_status' in kwargs:
            reg_options = (
                'tgt_region_status',
            )
            self.set_attributes( reg_options, kwargs )
