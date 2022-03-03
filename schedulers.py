from des import SchedulerDES


class FCFS(SchedulerDES):

    def scheduler_func(self, cur_event):
        print(cur_event)
        return self.processes[cur_event.process_id]

    def dispatcher_func(self, cur_process):
            cur_process.__process_state(2)
            time_used = cur_process.run_for(cur_process.remaining_time)
            cur_process.__process_state = ProcessStates.TERMINATED
            return Event(process_id = cur_process.process_id, event_type = EventPROC_CPU_DONE, event_time = cur_process.time )


class SJF(SchedulerDES):
    def scheduler_func(self, cur_event):
        pass

    def dispatcher_func(self, cur_process):
        pass


class RR(SchedulerDES):
    def scheduler_func(self, cur_event):
        pass

    def dispatcher_func(self, cur_process):
        pass


class SRTF(SchedulerDES):
    def scheduler_func(self, cur_event):
        pass

    def dispatcher_func(self, cur_process):
        pass
