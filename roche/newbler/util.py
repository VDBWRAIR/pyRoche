from projectdir import ProjectDirectory

from Bio import SeqIO

import sys
from glob import glob
from os.path import join, basename, dirname, splitext
import os.path
import os

def find_in_path( exe ):
    '''
        Looks for exe in sys.path and returns abs path
         to exe if found or None if not found

        @param exe - Executable to search for
    
        @returns absolute path to exe if found or None
    '''
    for path in os.environ['PATH'].split(':'):
        if os.path.exists( join( path, exe ) ):
            return join( path, exe )

def reference_file_for_identifier( identifier, projdir ):
    """
        Returns the reference file in a nebler project that an identifier comes from
        
        @param identifier - An identifier to obtain the reference file for. Can be the
            full identifier name or a part of it(Case insensitive)
        @param projdir - Project directory path
    
        @returns reference file path or None if not found
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
