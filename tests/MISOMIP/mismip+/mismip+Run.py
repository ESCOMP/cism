#!/usr/bin/env python

# This script runs any or all of the various MISMIP+ experiments.
# See this paper for details:
#   X. S. Asay-Davis et al. (2016), Experimental design for three interrelated 
#   marine ice sheet and ocean model intercomparison projects: 
#   MISMIP v. 3 (MISMIP+), ISOMIP v. 2 (ISOMIP+) and MISOMIP v. 1 (MISOMIP1),
#   Geosci. Model Devel., 9, 2471-2497, doi: 10.5194/gmd-9-2471-2016.

import sys, os
import fileinput
from optparse import OptionParser
from ConfigParser import ConfigParser
from netCDF4 import Dataset

# Parse options
optparser = OptionParser()

optparser.add_option('-e', '--exec', dest='executable', type = 'string', default='./cism_driver', help='Path to the CISM executable')
optparser.add_option("-x", "--expt", dest='experiment', type='string', default = 'allIce', help="MISMIP+ experiment(s) to run", metavar="EXPT")
optparser.add_option('-n', '--parallel', dest='parallel', type='int', help='Number of processors: if specified then run in parallel', metavar="NUMPROCS")


for option in optparser.option_list:
    if option.default != ("NO", "DEFAULT"):
        option.help += (" " if option.help else "") + "[default: %default]"
options, args = optparser.parse_args()

if options.experiment == 'Spinup':
    experiments = ['Spinup']
    print 'Run the MISMIP+ Spinup experiment'
#if options.experiment == 'all':
#    experiments = ['Spinup', 'Ice0', 'Ice1r', 'Ice1ra', 'Ice1rr', 'Ice2r', 'Ice2ra', 'Ice2rr', 'Ice1rax', 'Ice1rrx', 'Ice2rax', 'Ice2rrx']
#    print 'Run all the MISMIP+ experiments, including Spinup'
elif options.experiment == 'allIce':
    experiments = ['Ice0', 'Ice1r', 'Ice1ra', 'Ice1rr', 'Ice2r', 'Ice2ra', 'Ice2rr', 'Ice1rax', 'Ice1rrx', 'Ice2rax', 'Ice2rrx']
    print 'Run all the MISMIP+ experiments, excluding Spinup'
elif options.experiment == 'Ice1':
    experiments = ['Ice1r', 'Ice1ra', 'Ice1rr', 'Ice1rax', 'Ice1rrx']
    print 'Run the MISMIP+ Ice1 experiments'
elif options.experiment == 'Ice2':
    experiments = ['Ice2r', 'Ice2ra', 'Ice2rr', 'Ice2rax', 'Ice2rrx']
    print 'Run the MISMIP+ Ice2 experiments'
elif options.experiment in ['Ice0', 'Ice1r', 'Ice1ra', 'Ice1rr', 'Ice1rax', 'Ice1rrx', 'Ice2r', 'Ice2ra', 'Ice2rr', 'Ice2rax', 'Ice2rrx']:
    experiments = [options.experiment]
    print 'Run experiment', options.experiment
else:
    sys.exit('Please specify experiment(s) from this list: Spinup, allIce, Ice1, Ice2, Spinup, Ice0, Ice1r, Ice1ra, Ice1rr, Ice1rax, Ice1rrx, Ice2r, Ice2ra, Ice2rr, Ice2rax, Ice2rrx')

# Loop through experiments                                                                                                                                                        
for expt in experiments:
    print 'Running experiment', expt

    # Change to directory for this experiment
    os.chdir(expt)
    
    # Set config file
    configfile = 'mismip+' + expt + '.config'

    # Make sure we are starting from the final time slice of the input file,
    # (Except for Spinup, the input file is a restart file from a previous run.)

    if expt != 'Spinup':

        # Read the config file
        config = ConfigParser()
        config.read(configfile)

        # Edit the 'time' entry in the [CF input] section.
        inputfile = config.get('CF input', 'name')
        infile = Dataset(inputfile,'r')
        ntime = len(infile.dimensions['time'])
        config.set('CF input', 'time', ntime)
        print 'input file =', inputfile
        print 'time slice =', ntime
        infile.close()

        # Write the modified config file
        with open(configfile, 'w') as newconfigfile:
            config.write(newconfigfile)

    # Run CISM

    print 'parallel =', options.parallel

    if options.parallel == None:
        # Perform a serial run
        os.system(options.executable + ' ' + configfile)
    else:
        # Perform a parallel run
        if options.parallel <= 0:
            sys.exit( 'Error: Number of processors specified for parallel run is <=0.' )
        else:
            # These calls to os.system will return the exit status: 0 for success (the command exists), some other integer for failure
            if os.system('which openmpirun > /dev/null') == 0:
                mpiexec = 'openmpirun -np ' + str(options.parallel)
            elif os.system('which mpirun > /dev/null') == 0:
                mpiexec = 'mpirun -np ' + str(options.parallel)
            elif os.system('which aprun > /dev/null') == 0:
                mpiexec = 'aprun -n ' + str(options.parallel)
            elif os.system('which mpirun.lsf > /dev/null') == 0:
                # mpirun.lsf does NOT need the number of processors (options.parallel)
                mpiexec = 'mpirun.lsf'
            else:
                sys.exit('Unable to execute parallel run.  Please edit the script to use your MPI run command, or run manually with something like: mpirun -np 4 ./cism_driver mismip+Init.config')

            runstring = mpiexec + ' ' + options.executable + ' ' + configfile
            print 'Executing parallel run with:  ' + runstring + '\n\n'

            # Here is where the parallel run is actually executed!
            os.system(runstring)

    print 'Finished experiment', expt

    # Change to parent directory and continue
    os.chdir('..')