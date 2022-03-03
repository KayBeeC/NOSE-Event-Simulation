import logging
import math
import numbers
from bisect import insort
from collections import deque
from functools import partial

from numpy import random

from event import Event, EventTypes
from process import Process, ProcessStates


class SchedulerDES(object):
    """Implementation of a discrete event simulator (DES) for a process scheduling system.

    For the basics of DES, please see the AE specification.
    """

    def __init__(self, *, num_processes, arrivals_per_time_unit, avg_cpu_burst_time, context_switch_time=0.0,
                 quantum=math.inf):
        """Initialises a new SchedulerDiscreteEventSimulator object.

        Arguments:
        - num_processes: number of processes to simulate
        - arrivals_per_time_unit: rate of arrival of new processes (processes/time unit)
        - avg_cpu_burst_time: average duration of CPU bursts
        - context_switch_time: amount of time it takes to do a context switch (defaults to 0.0)
        - quantum: max amount of time for which to execute the selected process (defaults to math.inf, i.e., batch mode)
        """
        if not (isinstance(num_processes, int) and num_processes > 0):
            raise ValueError("Value {} not a positive (> 0) integer.".format(num_processes))
        if not (isinstance(arrivals_per_time_unit, numbers.Real) and arrivals_per_time_unit > 0.0):
            raise ValueError("Value {} not a positive (> 0) number.".format(arrivals_per_time_unit))
        if not (isinstance(avg_cpu_burst_time, numbers.Real) and avg_cpu_burst_time >= 0.0):
            raise ValueError("Value {} not a positive (> 0) number.".format(avg_cpu_burst_time))
        if not (isinstance(context_switch_time, numbers.Real) and context_switch_time >= 0.0):
            raise ValueError("Value {} not a positive (> 0) number.".format(context_switch_time))
        if not (isinstance(quantum, numbers.Real) and quantum > 0.0):
            raise ValueError("Value {} not a positive (> 0) number.".format(quantum))
        self.num_processes = num_processes
        self._arrivals_per_time_unit = arrivals_per_time_unit
        self._arrival_time = partial(random.exponential, 1.0 / arrivals_per_time_unit)  # Poisson inter-arrival time
        self._avg_cpu_burst_time = avg_cpu_burst_time
        self._service_time = partial(random.exponential, avg_cpu_burst_time)  # Exponential service time
        self.context_switch_time = context_switch_time
        self.quantum = quantum
        self._logger = logging.getLogger(__name__)
        self.process_on_cpu = None
        self.time = 0
        self.events_queue = deque()
        self.processes = list()

    def __reset(self):
        """Internal function to reset the simulator's state.
        """
        self.time = 0
        self.events_queue = deque()
        self.processes = list()
        self.process_on_cpu = None

    def print_events_queue(self, func=print):
        """Prints the contents of the events queue on screen.
        """
        for event in self.events_queue:
            func("    " + str(event))

    def __log_events_queue(self, level=logging.DEBUG):
        """Prints the contents of the events queue using logging.debug().
        """
        if not self._logger.isEnabledFor(level):
            return
        self.print_events_queue(partial(self._logger.log, level))

    def print_processes(self, func=print):
        """Prints the process table on screen.
        """
        for process in self.processes:
            func("    " + str(process))

    def __log_processes(self, level=logging.DEBUG):
        """Prints the process table using logging.debug() by default.
        """
        if not self._logger.isEnabledFor(level):
            return
        self.print_processes(partial(self._logger.log, level))

    def print_statistics(self):
        """Computes and prints execution time statistics.

        :rtype:
        """
        sum_turnaround_time = 0.0
        sum_waiting_time = 0.0
        for p in self.processes:
            sum_turnaround_time += p.turnaround_time()
            sum_waiting_time += p.waiting_time()
        print("    Avg. turnaround time: " + str(sum_turnaround_time / len(self.processes)))
        print("    Avg. waiting time: " + str(sum_waiting_time / len(self.processes)))

    def full_name(self):
        """Returns a string containing the current scheduler's name and configuration values.
        """
        return (self.__class__.__name__ +
                " [#Processes: " + str(self.num_processes) +
                ", Avg arrivals per time unit: " + str(self._arrivals_per_time_unit) +
                ", Avg CPU burst time: " + str(self._avg_cpu_burst_time) +
                ", Context switch time: " + str(self.context_switch_time) +
                (", Quantum: " + str(self.quantum) if self.quantum != math.inf else "") + "]")

    def simple_name(self):
        """Returns a string containing the current scheduler's name.
        """
        return self.__class__.__name__

    def generate_and_init(self, seed=None):
        """Generates the workload and initialises internal data structures.
        """
        self.__reset()
        random.seed(seed)
        cur_time = 0
        for i in range(self.num_processes):
            cur_time += self._arrival_time()
            new_process = Process(process_id=i, arrival_time=cur_time, service_time=self._service_time())
            self.processes.append(new_process)
            new_event = Event(process_id=new_process.process_id, event_time=cur_time,
                              event_type=EventTypes.PROC_ARRIVES)
            insort(self.events_queue, new_event)

    def next_event_time(self):
        """Returns the time of the first event after the current system time.
        """
        next_time = math.inf
        for event in self.events_queue:
            if event.event_time > self.time:
                next_time = event.event_time
                break
        return next_time

    def __update_process_states(self):
        """Used to update the status of processes based on the current time.
        """
        for p in self.processes:
            if p.arrival_time <= self.time and p.process_state == ProcessStates.NEW:
                p.process_state = ProcessStates.READY

    def run(self, seed=None):
        """Main implementation of DES.

        Parameters:
        - seed: Used to initialise the random number generator
        """
        self._logger.info(self.full_name() + " starting up...")

        # Generate workload (use optional user-defined seed for reproducibility)
        self.generate_and_init(seed)

        # Debug logging of process table
        self._logger.debug("Processes at time 0:")
        self.__log_processes()

        # While there are more events to process...
        while self.events_queue:
            # Debug logging of events queue
            self._logger.debug("Events queue at time " + str(self.time) + ":")
            self.__log_events_queue()

            # Remove the next event to be processed from the queue
            cur_event = self.events_queue.popleft()
            self._logger.debug("Processing event: " + str(cur_event) + " at time " + str(self.time))

            # Advance internal clock and update process states, if necessary
            if self.time < cur_event.event_time:
                self._logger.debug("Advancing time to " + str(cur_event.event_time))
                self.time = cur_event.event_time
            self.__update_process_states()

            # Debug logging of process table
            self._logger.info("Processes at time " + str(self.time) + ":")
            self.__log_processes(logging.INFO)

            # Run scheduler to select next process to execute
            process_to_run = self.scheduler_func(cur_event)
            if process_to_run is None:
                raise ValueError("Scheduler didn't select any process to run!!!")
            self._logger.info(
                "Next process to run: " + str(process_to_run.process_id) + " (prev: " + str(self.process_on_cpu) + ")")
            if process_to_run.process_state != ProcessStates.READY:
                raise ValueError(
                    "Process " + str(process_to_run) + " not in runnable state (" + str(process_to_run.process_state) + ").")

            # Advance the internal clock by the context switch time, if a
            # process different than the previously executing one was selected
            if process_to_run != self.process_on_cpu:
                self.process_on_cpu = process_to_run
                self.time += self.context_switch_time

            # Run the dispatcher to execute the selected process
            ret_event = self.dispatcher_func(process_to_run)

            # Add the resulting event to the queue and advance the internal clock, as appropriate
            self._logger.debug("Resulting event: " + str(ret_event))
            if ret_event.event_type != EventTypes.PROC_CPU_DONE:
                insort(self.events_queue, ret_event)
            self.time = ret_event.event_time
            self._logger.debug("Clock now at time: " + str(self.time))

        # Debug logging of process table
        self._logger.debug("Processes at time " + str(self.time) + ":")
        self.__log_processes()
        self._logger.info(self.simple_name() + " finished at time " + str(self.time))

    def scheduler_func(self, cur_event):
        """Processes the current event and returns the process to be executed next.

        This function should be overridden by the students as part of this AE.
        Note: the return value should be a Process object, not a process id.
        """
        pass

    def dispatcher_func(self, cur_process):
        """Executes the selected process and returns a new event.

        This function should be overridden by the students as part of this AE.
        Note: your function should make sure to update the process state as it goes.
        The returned event should be of type PROC_CPU_REQ if the process needs more
        time to finish, or PROC_CPU_DONE if the process terminated during the last
        execution.
        """
        pass
