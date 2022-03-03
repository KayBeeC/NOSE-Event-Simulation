import argparse
import logging
import sys

from numpy import random

from des import SchedulerDES
from schedulers import FCFS, SJF, RR, SRTF

# default values
seed = int.from_bytes(random.bytes(4), byteorder="little")
num_processes = 10
arrivals_per_time_unit = 3.0
avg_cpu_burst_time = 2
quantum = 0.5
context_switch_time = 0.0
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

# parse arguments
parser = argparse.ArgumentParser(description='NOSE2 AE2: Discrete Event Simulation')
parser.add_argument('--seed', '-S', help='PRNG random seed value', type=int)
parser.add_argument('--processes', '-P', help='Number of processes to simulate', default=num_processes, type=int)
parser.add_argument('--arrivals', '-L', help='Avg number of process arrivals per time unit',
                    default=arrivals_per_time_unit, type=float)
parser.add_argument('--cpu_time', '-c', help='Avg duration of CPU burst', default=avg_cpu_burst_time, type=float)
parser.add_argument('--cs_time', '-x', help='Duration of each context switch', default=context_switch_time, type=float)
parser.add_argument('--quantum', '-q', help='Duration of each quantum (Round Robin scheduling)', default=quantum,
                    type=float)
parser.add_argument('--verbose', '-v', help='Turn logging on; specify multiple times for more verbosity',
                    action='count')
args = parser.parse_args()
if args.seed:
    seed = args.seed
if args.verbose == 1:
    logging.getLogger().setLevel(logging.INFO)
elif args.verbose is not None:
    logging.getLogger().setLevel(logging.DEBUG)
num_processes = args.processes
arrivals_per_time_unit = args.arrivals
avg_cpu_burst_time = args.cpu_time
context_switch_time = args.cs_time
quantum = args.quantum

print("NOSE2 :: AE2 :: Scheduler Discrete Event Simulation")
print("---------------------------------------------------")

# print input specification
print("Using seed: " + str(seed))
base_sim = SchedulerDES(num_processes=num_processes, arrivals_per_time_unit=arrivals_per_time_unit,
                        avg_cpu_burst_time=avg_cpu_burst_time)
base_sim.generate_and_init(seed)
print("Processes to be executed:")
base_sim.print_processes()

# instantiate simulators
simulators = [FCFS(num_processes=num_processes, arrivals_per_time_unit=arrivals_per_time_unit,
                   avg_cpu_burst_time=avg_cpu_burst_time, context_switch_time=context_switch_time),
              SJF(num_processes=num_processes, arrivals_per_time_unit=arrivals_per_time_unit,
                  avg_cpu_burst_time=avg_cpu_burst_time, context_switch_time=context_switch_time),
              RR(num_processes=num_processes, arrivals_per_time_unit=arrivals_per_time_unit,
                 avg_cpu_burst_time=avg_cpu_burst_time, context_switch_time=context_switch_time, quantum=quantum),
              SRTF(num_processes=num_processes, arrivals_per_time_unit=arrivals_per_time_unit,
                   avg_cpu_burst_time=avg_cpu_burst_time, context_switch_time=context_switch_time)]

# run simulators
for sim in simulators:
    print("-----")
    print(sim.full_name() + ":")
    logging.info("--- " + sim.full_name() + " ---")
    sim.run(seed)
    sim.print_statistics()
