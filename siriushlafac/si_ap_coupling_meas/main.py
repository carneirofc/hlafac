"""Main module of the Application Interface."""
import os as _os
import logging as _log
from threading import Thread
import pathlib as _pathlib

import numpy as np
import matplotlib.pyplot as mplt
import matplotlib.gridspec as mgs
from matplotlib import rcParams

from qtpy.QtCore import Qt
from qtpy.QtGui import QDoubleValidator
from qtpy.QtWidgets import QWidget, QPushButton, QGridLayout, QSpinBox, \
    QLabel, QGroupBox, QLineEdit, QComboBox, QHBoxLayout, QFileDialog, \
    QVBoxLayout

import qtawesome as qta

# from pydm.widgets.logdisplay import PyDMLogDisplay

from siriuspy.envars import VACA_PREFIX
from siriuspy.namesys import SiriusPVName

from siriushla import util
from siriushla.widgets import MatplotlibWidget, SiriusMainWindow, \
    SiriusLogDisplay, SiriusSpinbox, SiriusLabel

from apsuite.commisslib.meas_coupling_tune import MeasCoupling

rcParams.update({
    'font.size': 12, 'axes.grid': True, 'grid.linestyle': '--',
    'grid.alpha': 0.5})


class SICoupMeasWindow(SiriusMainWindow):
    """."""
    EXT = 'pickle'
    EXT_FLT = f'Pickle Files (*.{EXT:s})'
    DEFAULT_DIR = _pathlib.Path.home().as_posix()
    DEFAULT_DIR += _os.path.sep + _os.path.join(
        'mounts', 'screens-iocs', 'data_by_day')
    print(DEFAULT_DIR)

    def __init__(self, parent=None):
        """."""
        super().__init__(parent=parent)
        self.meas_coup = MeasCoupling()
        self._last_dir = self.DEFAULT_DIR

        self.setupui()
        self.setObjectName('SIApp')
        color = util.get_appropriate_color('SI')
        icon = qta.icon('mdi.notebook', 'mdi.pulse', options=[
            dict(scale_factor=0.5, color=color, offset=(0.2, -0.3)),
            dict(scale_factor=1, color=color, offset=(0, 0.0))])
        self.setWindowIcon(icon)
        self.resize(1100, 700)

    def setupui(self):
        """."""
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle("SI - Coupling Measurement")
        self.setDocumentMode(False)
        self.setDockNestingEnabled(True)

        mwid = self._create_central_widget()
        self.setCentralWidget(mwid)

    def _create_central_widget(self):
        wid = QWidget(self)
        wid.setLayout(QGridLayout())

        wid.layout().addWidget(
            QLabel(f'<h1>SI - Coupling Measurement </h1>', wid),
            0, 0, 1, 2, alignment=Qt.AlignCenter)

        ctrls = self.get_param_control_widget(wid)
        anal = self.get_analysis_control_widget(wid)
        status = self.get_measurement_status_widget(wid)
        fig_wid = self.make_figure(wid)
        saveload = self.get_saveload_widget(wid)

        wid.layout().addWidget(ctrls, 1, 0)
        wid.layout().addWidget(anal, 2, 0)
        wid.layout().addWidget(status, 3, 0)
        # wid.layout().addWidget(fig_wid, 1, 1, 3, 1)
        # wid.layout().addWidget(saveload, 3, 0)
        lay = QVBoxLayout()
        lay.addWidget(saveload)
        lay.addWidget(fig_wid)
        wid.layout().addLayout(lay, 1, 1, 3, 1)
        wid.layout().setRowStretch(3, 10)
        return wid

    def make_figure(self, parent):
        """."""
        self.fig = mplt.figure(figsize=(7, 14))
        fig_widget = MatplotlibWidget(self.fig, parent=parent)

        gs = mgs.GridSpec(1, 1)
        gs.update(
            left=0.125, right=0.97, bottom=0.13, top=0.9,
            hspace=0.5, wspace=0.35)
        self.axes = self.fig.add_subplot(gs[0, 0])

        self.axes.set_xlabel('Current [A]')
        self.axes.set_ylabel('Transverse Tunes')
        self.axes.set_title(
            'Transverse Linear Coupling: ({:.2f} ± {:.2f}) %'.format(0, 0),
            fontsize='x-large')

        # plot meas data
        self.line_tune1 = self.axes.plot(
            [], [], 'o', color='C0', label=r'$\nu_1$')[0]
        self.line_tune2 = self.axes.plot(
            [], [], 'o', color='C1', label=r'$\nu_2$')[0]

        # plot fitting
        self.line_fit1 = self.axes.plot(
            [], [], color='tab:gray', label='fitting')[0]
        self.line_fit2 = self.axes.plot(
            [], [], color='tab:gray')[0]
        self.axes.legend(loc='best')
        return fig_widget

    def get_param_control_widget(self, parent):
        """."""
        wid = QGroupBox('Measurement Control', parent)
        wid.setLayout(QGridLayout())

        self.wid_quadfam = QComboBox(wid)
        self.wid_quadfam.addItems(self.meas_coup.params.QUADS)
        self.wid_quadfam.setCurrentText(self.meas_coup.params.quadfam_name)
        self.wid_quadfam.currentTextChanged.connect(self._update_quadcurr_wid)

        self._currpvname = SiriusPVName(
            'SI-Fam:PS-'+self.meas_coup.params.quadfam_name+':Current-SP')
        self._currpvname = self._currpvname.substitute(prefix=VACA_PREFIX)
        self.wid_quadcurr_sp = SiriusSpinbox(self, self._currpvname)
        self.wid_quadcurr_sp.showStepExponent = False
        self.wid_quadcurr_mn = SiriusLabel(
            self, self._currpvname.substitute(propty_suffix='Mon'))
        self.wid_quadcurr_mn.showUnits = True

        self.wid_nr_points = QSpinBox(wid)
        self.wid_nr_points.setValue(self.meas_coup.params.nr_points)

        self.wid_time_wait = QLineEdit(wid)
        self.wid_time_wait.setText(str(self.meas_coup.params.time_wait))
        self.wid_time_wait.setValidator(QDoubleValidator())

        self.wid_neg_percent = QLineEdit(wid)
        self.wid_neg_percent.setText(
            str(self.meas_coup.params.neg_percent*100))
        self.wid_neg_percent.setValidator(QDoubleValidator())

        self.wid_pos_percent = QLineEdit(wid)
        self.wid_pos_percent.setText(
            str(self.meas_coup.params.pos_percent*100))
        self.wid_pos_percent.setValidator(QDoubleValidator())

        pusb_start = QPushButton(qta.icon('mdi.play'), 'Start', wid)
        pusb_start.clicked.connect(self.start_meas)
        pusb_stop = QPushButton(qta.icon('mdi.stop'), 'Stop', wid)
        pusb_stop.clicked.connect(self.meas_coup.stop)

        wid.layout().addWidget(QLabel('Quadrupole Family Name', wid), 1, 1)
        wid.layout().addWidget(QLabel('Quadrupole Current [A]', wid), 2, 1)
        wid.layout().addWidget(QLabel('# of Points', wid), 4, 1)
        wid.layout().addWidget(QLabel('Time to wait [s]', wid), 5, 1)
        wid.layout().addWidget(QLabel('Current Lower Limit [%]', wid), 6, 1)
        wid.layout().addWidget(QLabel('Current Upper Limit [%]', wid), 7, 1)
        wid.layout().addWidget(self.wid_quadfam, 1, 2)
        wid.layout().addWidget(self.wid_quadcurr_sp, 2, 2)
        wid.layout().addWidget(self.wid_quadcurr_mn, 3, 2)
        wid.layout().addWidget(self.wid_nr_points, 4, 2)
        wid.layout().addWidget(self.wid_time_wait, 5, 2)
        wid.layout().addWidget(self.wid_neg_percent, 6, 2)
        wid.layout().addWidget(self.wid_pos_percent, 7, 2)
        lay = QHBoxLayout()
        lay.addStretch()
        lay.addWidget(pusb_start)
        lay.addStretch()
        lay.addWidget(pusb_stop)
        lay.addStretch()
        wid.layout().addLayout(lay, 9, 1, 1, 2)
        wid.layout().setColumnStretch(0, 2)
        wid.layout().setColumnStretch(3, 2)
        return wid

    def get_analysis_control_widget(self, parent):
        wid = QGroupBox('Analysis Control', parent)
        wid.setLayout(QGridLayout())
        self.wid_coupling_resolution = QLineEdit(wid)
        self.wid_coupling_resolution.setText(
            str(self.meas_coup.params.coupling_resolution*100))
        self.wid_coupling_resolution.setValidator(QDoubleValidator())
        self.wid_coupling_resolution.setStyleSheet('max-width:5em;')

        pusb_proc = QPushButton(qta.icon('mdi.chart-line'), 'Process', wid)
        pusb_proc.clicked.connect(self._plot_results)

        wid.layout().addWidget(QLabel('Coupling Resolution [%]', wid), 0, 0)
        wid.layout().addWidget(self.wid_coupling_resolution, 0, 1)
        wid.layout().addWidget(pusb_proc, 0, 3)
        wid.layout().setColumnStretch(2, 5)
        return wid

    def get_measurement_status_widget(self, parent):
        """."""
        wid = QGroupBox('Measurement Status', parent)
        wid.setLayout(QGridLayout())

        self.log_label = SiriusLogDisplay(wid, level=_log.INFO)
        self.log_label.logFormat = '%(message)s'
        wid.layout().addWidget(self.log_label, 0, 0)
        return wid

    def get_saveload_widget(self, parent):
        """."""
        svld_wid = QGroupBox('Save and Load', parent)
        svld_lay = QGridLayout(svld_wid)

        pbld = QPushButton('Load', svld_wid)
        pbld.setIcon(qta.icon('mdi.file-upload-outline'))
        pbld.setToolTip('Load data from file')
        pbld.clicked.connect(self._load_data_from_file)

        pbsv = QPushButton('Save', svld_wid)
        pbsv.setIcon(qta.icon('mdi.file-download-outline'))
        pbsv.setToolTip('Save data to file')
        pbsv.clicked.connect(self._save_data_to_file)
        self.loaded_label = QLabel('', svld_wid)
        self.loaded_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        svld_lay.addWidget(pbsv, 0, 0)
        svld_lay.addWidget(pbld, 1, 0)
        svld_lay.addWidget(self.loaded_label, 0, 1, 2, 1)
        svld_lay.setColumnStretch(1, 2)
        return svld_wid

    def _save_data_to_file(self, _):
        filename = QFileDialog.getSaveFileName(
            caption='Define a File Name to Save Data',
            directory=self._last_dir,
            filter=self.EXT_FLT)
        fname = filename[0]
        if not fname:
            return
        self._last_dir, _ = _os.path.split(fname)
        self.loaded_label.setText('')
        fname += '' if fname.endswith(self.EXT) else ('.' + self.EXT)
        self.meas_coup.save_data(fname, overwrite=True)

    def _load_data_from_file(self):
        filename = QFileDialog.getOpenFileName(
            caption='Select a Coupling Data File.',
            directory=self._last_dir,
            filter=self.EXT_FLT)
        fname = filename[0]
        if not fname:
            return
        self._last_dir, _ = _os.path.split(fname)

        self.meas_coup.load_and_apply_old_data(fname)
        splitted = fname.split('/')
        stn = splitted[0]
        leng = len(stn)
        for s in splitted[1:]:
            if leng + len(s) > 90:
                stn += '/\n' + s
                leng = len(s)
            else:
                stn += '/' + s
                leng += len(s)
        self.loaded_label.setText('File Loaded: \n' + stn)

        self.wid_quadfam.setCurrentIndex(
            self.meas_coup.params.QUADS.index(
                self.meas_coup.params.quadfam_name))
        self.wid_nr_points.setValue(self.meas_coup.params.nr_points)
        self.wid_time_wait.setText(str(self.meas_coup.params.time_wait))
        self.wid_neg_percent.setText(
            str(self.meas_coup.params.neg_percent*100))
        self.wid_pos_percent.setText(
            str(self.meas_coup.params.pos_percent*100))
        self.wid_coupling_resolution.setText(
            str(self.meas_coup.params.coupling_resolution*100))

        self._plot_results()

    def _adjust_tune(self):
        tunex_goal = float(self.wid_nux.value())
        tuney_goal = float(self.wid_nuy.value())

        self.tunecorr.get_tunes(self.fit_traj.model)
        tunemat = self.tunecorr.calc_jacobian_matrix()
        self.tunecorr.correct_parameters(
            model=self.fit_traj.model,
            goal_parameters=np.array([tunex_goal, tuney_goal]),
            jacobian_matrix=tunemat)

        self.lab_tune.setText('Done!')

    def start_meas(self):
        """."""
        if self.meas_coup.ismeasuring:
            _log.error('There is another measurement happening.')
            return
        Thread(target=self._do_meas, daemon=True).start()

    def _do_meas(self):

        self.meas_coup.params.quadfam_name = self.wid_quadfam.currentText()
        self.meas_coup.params.nr_points = int(self.wid_nr_points.value())
        self.meas_coup.params.time_wait = float(self.wid_time_wait.text())
        self.meas_coup.params.neg_percent = float(
            self.wid_neg_percent.text()) / 100
        self.meas_coup.params.pos_percent = float(
            self.wid_pos_percent.text()) / 100

        self.loaded_label.setText('')

        self.meas_coup.wait_for_connection()
        self.meas_coup.start()
        self.meas_coup.wait_measurement()
        self._plot_results()

    def _process_data(self):
        try:
            self.meas_coup.process_data()
        except Exception as err:
            _log.error('Problem processing data.')
            _log.error(str(err))

    def _plot_results(self):
        self.meas_coup.params.coupling_resolution = float(
            self.wid_coupling_resolution.text()) / 100
        self._process_data()
        anl = self.meas_coup.analysis
        if 'qcurr' not in anl:
            _log.error('There is no data to plot.')
            return
        qcurr, tune1, tune2 = anl['qcurr'], anl['tune1'], anl['tune2']
        self.line_tune1.set_xdata(qcurr)
        self.line_tune2.set_xdata(qcurr)
        self.line_tune1.set_ydata(tune1)
        self.line_tune2.set_ydata(tune2)
        self.axes.set_xlabel(f'{self.meas_coup.data["qname"]} Current [A]')

        if 'fitted_param' in anl:
            fit_vec = anl['fitted_param']['x']
            fittune1, fittune2, qcurr_interp = self.meas_coup.get_normal_modes(
                params=fit_vec, curr=qcurr, oversampling=10)

            self.line_fit1.set_xdata(qcurr_interp)
            self.line_fit2.set_xdata(qcurr_interp)
            self.line_fit1.set_ydata(fittune1)
            self.line_fit2.set_ydata(fittune2)
            self.axes.set_title(
                'Transverse Linear Coupling: ({:.2f} ± {:.2f}) %'.format(
                    fit_vec[-1]*100, anl['fitting_error'][-1] * 100))
        else:
            self.line_fit1.set_xdata([])
            self.line_fit2.set_xdata([])
            self.line_fit1.set_ydata([])
            self.line_fit2.set_ydata([])
            self.axes.set_title('Transverse Linear Coupling: (Nan ± Nan) %')

        self.axes.relim()
        self.axes.autoscale_view()
        self.fig.canvas.draw()

    def _update_quadcurr_wid(self, text):
        self._currpvname = self._currpvname.substitute(dev=text)
        self.wid_quadcurr_sp.channel = self._currpvname
        self.wid_quadcurr_mn.channel = self._currpvname.substitute(
            propty_suffix='Mon')
