from PyQt5.QtWidgets import *
from PyQt5 import uic
import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

form_class = uic.loadUiType("DAQ.ui")[0]


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.isRun = True
        self.RunBtn.clicked.connect(self.ToggleRun)

        self.fig = plt.Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("ms")
        self.ax.set_ylabel("Voltage")
        self.x = [0, 1]
        self.y = [0, 1]
        self.line, = self.ax.plot(self.x, self.y, "r")
        self.canvas = FigureCanvas(self.fig)
        self.Figure.addWidget(self.canvas)

        self.DAQ()

    def drawPlot(self):
        self.line.set_xdata(self.x)
        self.line.set_ydata(self.y)
        if self.XminAuto.isChecked():
            xmin = self.x[0]
        else:
            xmin = self.XminValue.value()
        if self.XmaxAuto.isChecked():
            xmax = self.x[len(self.x)-1]
        else:
            xmax = self.XmaxValue.value()

        self.ax.set_xlim(xmin, xmax)
        self.ax.set_ylim(min(self.y), max(self.y))
        self.canvas.draw()

    def ToggleRun(self):
        if self.isRun:
            self.isRun = False
            self.RunBtn.setText("Run")
        else:
            self.isRun = True
            self.RunBtn.setText("Stop")

    def FreqDomain(self):
        fs = 10000
        dt = 1/fs
        N = len(self.y)

        df = fs/N
        f = np.arange(0, N)*df
        timeY = np.array(self.y)
        freqY = np.fft.fft(timeY)*dt

        self.x = f[0:int(N/2 + 1)]
        self.y = np.abs(freqY[0:int(N/2 + 1)])

    def DAQ(self):
        global task
        task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0")
        task.timing.cfg_samp_clk_timing(rate=10000,
                                        sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                        samps_per_chan=1000)

        def callback(task_handle, every_n_samples_event_type,
                     number_of_samples, callback_data):
            self.y = task.read(number_of_samples_per_channel=1000)
            self.x = np.array(range(len(self.y)))/10    # 샘플 하나당 0.1ms
            if self.isRun:
                if self.Freq.isChecked():
                    self.FreqDomain()
                    self.ax.set_xlabel("Hz")
                else:
                    self.ax.set_xlabel("ms")
                self.drawPlot()
            return 0

        task.register_every_n_samples_acquired_into_buffer_event(1000, callback)
        task.start()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
    task.close()
    sys.exit()
