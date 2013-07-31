from nose.tools import eq_, raises
from .. import newblermetrics
from os.path import join, dirname

# Path to Newbler metrics
import fixtures
filepath = join( dirname( fixtures.PATH ), 'example_files', '454NewblerMetrics.txt' )

runmetrics = '''
runMetrics
{
    numberOfReferenceSequences  = 8;
    totalReferenceNumberOfBases = 13138;

    inputFileNumReads  = 11332; 
    inputFileNumBases  = 8424488; 

    totalNumberOfReads = 11327; 
    totalNumberOfBases = 8102117; 

    numberSearches   = 11179;
    seedHitsFound    = 164866, 14.75;
    overlapsFound    = 24288, 2.17, 14.73%;
    overlapsReported = 16935, 1.51, 69.73%;
    overlapsUsed     = 10741, 0.96, 63.42%;
}
'''
runmetrics_expected =  {
    'numberOfReferenceSequences': 8,
    'totalReferenceNumberOfBases': 13138,
    'inputFileNumReads': 11332,
    'inputFileNumBases': 8424488,
    'totalNumberOfReads': 11327,
    'totalNumberOfBases': 8102117,
    'numberSearches': 11179,
    'seedHitsFound': (164866, 14.75),
    'overlapsFound': (24288, 2.17, 14.73),
    'overlapsReported': (16935, 1.51, 69.73),
    'overlapsUsed': (10741, 0.96, 63.42)
}
readstatus = '''                 
    readStatus
	{
		numMappedReads    = 10741, 94.83%, 94.78%;
		numMappedBases    = 5909721, 72.94%, 70.15%;
		inferredReadError = 8.11%, 479299;

		numberFullyMapped     = 613, 5.41%, 5.41%;
		numberPartiallyMapped = 4325, 38.18%, 38.17%;
		numberUnmapped        = 438, 3.87%, 3.87%;
		numberRepeat          = 1, 0.01%, 0.01%;
		numberChimeric        = 5802, 51.22%, 51.20%;
		numberTooShort        = 148, 1.31%, 1.31%;
    }
'''
readstatus_expected = {
    'numMappedReads': (10741, 94.83, 94.78),
    'numMappedBases': (5909721, 72.94, 70.15),
    'inferredReadError': (8.11, 479299),
    'numberFullyMapped': (613, 5.41, 5.41),
    'numberPartiallyMapped': (4325, 38.18, 38.17),
    'numberRepeat': (1, 0.01, 0.01),
    'numberChimeric': (5802, 51.22, 51.20),
    'numberTooShort': (148, 1.31, 1.31)
}

def dicteq_( dict1, dict2 ):
    for k,v in dict1.iteritems():
        assert k in dict2, "{} not in {}".format(k,dict2)
        eq_( v, dict2[k] )

nm = newblermetrics.NewblerMetrics( filepath )

class TestParseMetrics( object ):
    def test_runmetrics( self ):
        dicteq_( runmetrics_expected, nm.parse_metrics( 'runMetrics' ) )

    def test_runmetricsgetattr( self ):
        return
        dicteq_( runmetrics_expected, nm.runMetrics )

    def test_readstatus( self ):
        dicteq_( readstatus_expected, nm.parse_metrics( 'readStatus' ) )

    def test_readstatusgetattr( self ):
        return
        dicteq_( readstatus_expected, nm.readStatus )

class TestParseSection( object ):
    def test_runMetrics( self ):
        ''' Just test the fixed value above '''
        dicteq_( runmetrics_expected, nm.parse_section( runmetrics ) )

    def test_readstatus( self ):
        dicteq_( readstatus_expected, nm.parse_section( readstatus ) )
