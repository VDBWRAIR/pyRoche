from roche.newbler import ProjectDirectory

from argparse import ArgumentParser
import csv
import pprint
import sys

DEFAULT_HEADERS = [
    'totalNumberOfReads',
    'totalNumberOfBases',
    'numAlignedReads',
    'numAlignedBases',
    'numberOfContigs',
    'numberOfBases',
    'numberOfLargeContigs',
    'numberOfLargeBases',
    'avgContigSize',
    'N50ContigSize',
    'largestContigSize'
]

def main( ):
    args = parse_args()
    denovo_stats_csv( stats( args.projdir ), args.headers )

def denovo_stats_csv( stats, wanted_headers ):
    w = csv.DictWriter( sys.stdout, wanted_headers, restval='N/A', extrasaction='ignore' )
    sys.stdout.write( "GsProject," )
    w.writeheader()
    for proj, stats in stats.iteritems():
        sys.stdout.write( "{},".format(proj) )
        w.writerow( stats )

def stats( projectlist ):
    '''
        Return dictionary of statistics per project directory name
        
        @param projectlist - List of project paths
        @returns dictonary keyed by project path with statistics from stats_forproj
    '''
    stats = {}
    for path in projectlist:
        stats[path] = stats_forproj( ProjectDirectory( path ) )

    return stats

def stats_forproj( proj ):
    '''
        Return all stats wanted for a project

        @param proj - roche.newbler.ProjectDirectory instance
        @returns dictionary of stats for Jun Hang
    '''
    stats = {}
    failcount = 0
    for group in ('runMetrics', 'readStatus', 'allContigMetrics'):
        try:
            stats.update( **proj.NewblerMetrics.parse_metrics( group ) )
        except ValueError as e:
            failcount += 1
            continue

    try:
        lcm = proj.NewblerMetrics.parse_metrics( 'largeContigMetrics' )
    except ValueError as e:
        failcount += 1

    # Return empty dictionary if non of the stats were available
    if failcount == 4:
        return {}
        
    stats['numberOfLargeContigs'] = lcm['numberOfContigs']
    stats['numberOfLargeBases'] = lcm['numberOfBases']
    del lcm['numberOfBases']
    del lcm['numberOfContigs']
    stats.update( **lcm )

    return stats

def parse_args():
    parser = ArgumentParser( description='Reports statistics on a denovo GsAssembly project' )

    parser.add_argument( dest='projdir', nargs='+', help='GsAssembly project path or list of them' )
    parser.add_argument( '--headers', dest='headers', nargs='+', default=DEFAULT_HEADERS, help='What NewblerMetrics to report' )

    return parser.parse_args()
