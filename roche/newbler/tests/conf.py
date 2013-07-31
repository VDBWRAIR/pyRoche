import os
import os.path

mapping_projects = [ "05_11_2012_1_TI-MID10_PR_2357_AH3", "05_11_2012_1_TI-MID51_PR_2305_pH1N1", "08_06_2012_1_Ti-MID30_D84_140_Dengue3"]
assembly_projects = ["08_31_2012_3_RL10_600Yu_10_VOID"]
all_projects = mapping_projects + assembly_projects

fileparsers = ['AlignmentInfo', 'NewblerProgress', 'NewblerMetrics']
files = ['454AlignmentInfo.tsv', '454NewblerProgress.txt', '454NewblerMetrics.txt']

mapping_fp = fileparsers + ['RefStatus','MappingProject','MappingQC']
mapping_files = files + ['454RefStatus','454MappingProject.xml', '454MappingQC.xls']

assembly_fp = fileparsers
assembly_files = files + ['454AssemblyProjext.xml']

tests_dir = os.path.dirname( os.path.abspath( __file__ ) )
examples_dir = os.path.join( os.path.dirname( tests_dir ), 'examples' )
ref_dir = os.path.join( examples_dir, 'Ref' )
