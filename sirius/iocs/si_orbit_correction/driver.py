
import queue
from pcaspy import Driver
import epics
from time import sleep
import api_correction as _api_correction


class PCASDriver(Driver):

    def  __init__(self, threads_dic, start_event, stop_event, interval):
        super().__init__()
        self._threads_dic = threads_dic
        self._interval = interval
        self._start_event = start_event
        self._queue = queue.Queue()
        self._stop_event = stop_event
        for tn in threads_dic:
            self._threads_dic[tn]._driver = self

    def read(self, reason):
        return super().read(reason)

    def write(self, reason, value):
        if reason == 'SICO-SOFB-MODE':
            if value == 0:
                self._threads_dic['orbit_correction']._mode = value
                if self._threads_dic['respm_measurement']._mode != value: self._threads_dic['respm_measurement']._interrupt_measrespm_event.set()
                else: self._threads_dic['respm_measurement']._mode = value
            elif value >= 1 and value <= 8:
                if self._threads_dic['respm_measurement']._mode != 0:
                    self.setParam('SICO-SOFB-ERROR', 7)
                    return
                else:
                    if self._threads_dic['var_update']._mode != 0:
                        self._threads_dic['orbit_correction']._mode = 'W_'+str(value)
                    else:
                        self._threads_dic['orbit_correction']._mode = value
            elif value >= 9 and value <= 14:
                if self._threads_dic['orbit_correction']._mode != 0:
                    self.setParam('SICO-SOFB-ERROR', 1)
                    return
                else:
                    if self._threads_dic['var_update']._mode != 0:
                        self._threads_dic['respm_measurement']._mode = 'W_'+str(value)
                    else:
                        self._threads_dic['respm_measurement']._mode = value
        elif reason == 'SICO-SOFB-AVGORBIT-NUMSAMPLES':
            if value > self._threads_dic['orbit_measurement']._max_length:
                self.setParam('SICO-SOFB-ERROR', 2)
                return
            else:
                self._threads_dic['orbit_measurement']._n_samples = value
        elif reason == 'SICO-SOFB-RESPM-SEL':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 8)
                return
            else:
                self._threads_dic['var_update']._mode = 4
        elif reason == 'SICO-SOFB-REFORBIT-X-SEL':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 9)
                return
            else:
                self._threads_dic['var_update']._mode = 5
        elif reason == 'SICO-SOFB-REFORBIT-Y-SEL':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 9)
                return
            else:
                self._threads_dic['var_update']._mode = 6
        elif reason == 'SICO-SOFB-RESPM':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 4)
                return
            else:
                self._threads_dic['var_update']._mode = 1
        elif reason == 'SICO-SOFB-REFORBIT-X':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 5)
                return
            else:
                self._threads_dic['var_update']._mode = 2
        elif reason == 'SICO-SOFB-REFORBIT-Y':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 5)
                return
            else:
                self._threads_dic['var_update']._mode = 3
        elif reason == 'SICO-SOFB-BPM-SEL':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 12)
                return
            else:
                self._threads_dic['var_update']._mode = 7
        elif reason == 'SICO-SOFB-CH-SEL':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 12)
                return
            else:
                self._threads_dic['var_update']._mode = 8
        elif reason == 'SICO-SOFB-CV-SEL':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 12)
                return
            else:
                self._threads_dic['var_update']._mode = 9
        elif reason == 'SICO-SOFB-BPM-ADD':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 12)
                return
            else:
                self._threads_dic['var_update']._mode = 10
        elif reason == 'SICO-SOFB-CH-ADD':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 12)
                return
            else:
                self._threads_dic['var_update']._mode = 11
        elif reason == 'SICO-SOFB-CV-ADD':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 12)
                return
            else:
                self._threads_dic['var_update']._mode = 12
        elif reason == 'SICO-SOFB-BPM-RMV':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 12)
                return
            else:
                self._threads_dic['var_update']._mode = 13
        elif reason == 'SICO-SOFB-CH-RMV':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 12)
                return
            else:
                self._threads_dic['var_update']._mode = 14
        elif reason == 'SICO-SOFB-CV-RMV':
            if self._threads_dic['orbit_correction']._mode != 0 or self._threads_dic['var_update']._mode != 0:
                self.setParam('SICO-SOFB-ERROR', 12)
                return
            else:
                self._threads_dic['var_update']._mode = 15
        elif reason == 'SICO-SOFB-WEIGHT':
            if not 0 <= value <= 1:
                self.setParam('SICO-SOFB-ERROR', 14)
                return
        return super().write(reason, value)
