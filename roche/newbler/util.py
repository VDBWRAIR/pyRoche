from projectdir import ProjectDirectory

from Bio import SeqIO

def reference_file_for_identifier( identifier, projdir ):
    """
        Arguments:
            identifier -- An identifier from 454RefStatus.txt to obtain the reference file for
    
        Return:
            reference file path or None if not found

        Tests:
            >>> this_dir = os.path.dirname( os.abspath( __file__ ) )
            >>> r = os.path.join( this_dir, 'Ref/pdmH1N1_California.fasta' )
            >>> fr = reference_file_for_identifier( 'california', 'examples/05_11_2012_1_TI-MID10_PR_2357_AH3' )
            >>> r == fr
            True
            >>> fr = reference_file_for_identifier( 'FJ969514_NS_California04', 'examples/05_11_2012_1_TI-MID51_PR_2305_pH1N1' )
            >>> r = fr
            True
            >>> reference_file_for_identifier( 'yankydoodle', 'examples/05_11_2012_1_TI-MID51_PR_2305_pH1N1' ) is None
            True
    """
    pd = ProjectDirectory( projdir )
    mp = pd.MappingProject
    refs = mp.get_reference_files()

    useref=None
    for ref in refs:
        refpath = ref
        try:
            for seq in SeqIO.parse( refpath, 'fasta' ):
                if identifier.lower() in seq.id.lower():
                    return refpath
        except IOError as e:
            sys.stderr.write( "Cannot read %s" % refpath )
            raise e
