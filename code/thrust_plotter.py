import sys
import serial
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

class ThrustStandApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rocket Motor Thrust Stand")
        self.setGeometry(100, 100, 800, 600)

        # Serial connection setup
        self.ser = serial.Serial('/dev/tty.usbserial-0001', 115200, timeout=1)

        # Data storage
        self.times = []
        self.thrusts = []

        # Create widgets
        self.graph_widget = pg.PlotWidget()
        self.tare_button = QPushButton("Tare")
        self.start_button = QPushButton("Start")
        self.export_button = QPushButton("Export CSV")

        # Set up layout
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.tare_button)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.export_button)
        layout.addWidget(self.graph_widget)
        layout.addLayout(button_layout)

        # Create a central widget and set the layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Connect buttons to functions
        self.tare_button.clicked.connect(self.tare_scale)
        self.start_button.clicked.connect(self.toggle_scale)
        self.export_button.clicked.connect(self.export_csv)

        # Set up timer for updating the graph
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(100)  # Update every 100 ms

        # Initialize scale state
        self.scale_on = False

    def send_command(self, command):
        self.ser.write(command.encode() + b'\n')

    def tare_scale(self):
        self.send_command("TARE")

    def toggle_scale(self):
        self.scale_on = not self.scale_on
        self.start_button.setText("Stop" if self.scale_on else "Start")
        self.send_command("START" if self.scale_on else "STOP")
    
    def read_serial_data(self):
        try:
            line = self.ser.readline()
            data = line.decode('ascii').strip().split(',')
            if len(data) == 2:
                return list(map(float, data))
        except (UnicodeDecodeError, ValueError):
            pass
        return None

    def update_graph(self):
        data = self.read_serial_data()
        if data:
            thrust, time = data
            print(f"thrust : {thrust}, time : {time}")
            self.thrusts.append(thrust)
            self.times.append(time)
            self.graph_widget.plot(self.times, self.thrusts, clear=True, pen=pg.mkPen(color=(245, 66, 66), width=5))

    def export_csv(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if filename:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Time', 'Thrust'])
                for time, thrust in zip(self.times, self.thrusts):
                    writer.writerow([time, thrust])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ThrustStandApp()
    window.show()
    sys.exit(app.exec_())