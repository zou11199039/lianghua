# -*- coding: utf-8 -*-
import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from datetime import datetime

# Import backend modules
# (Assuming main.py sets up paths correctly, or we use relative imports if run as module)


class WorkerThread(QThread):
    """Background thread to run the trading loop or long tasks."""

    log_signal = pyqtSignal(str)

    def __init__(self, system_controller):
        super().__init__()
        self.controller = system_controller
        self.running = True

    def run(self):
        self.log_signal.emit("Worker thread started.")
        # Simulation of a trading loop
        while self.running:
            # check schedule
            # if time matches, run strategy
            self.sleep(1)  # simple sleep for now

    def stop(self):
        self.running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enterprise QMT Quant System")
        self.resize(1000, 700)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main Layout
        main_layout = QHBoxLayout(central_widget)

        # Left Panel (Controls & Status)
        left_panel = QVBoxLayout()

        # 1. Control Group
        control_group = QGroupBox("System Control")
        control_layout = QVBoxLayout()
        self.btn_start = QPushButton("Start System")
        self.btn_stop = QPushButton("Stop System")
        self.btn_run_strategy = QPushButton("Force Run Strategy")

        self.btn_start.clicked.connect(self.start_system)
        self.btn_stop.clicked.connect(self.stop_system)
        self.btn_run_strategy.clicked.connect(self.force_run)

        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        control_layout.addWidget(self.btn_run_strategy)
        control_group.setLayout(control_layout)

        # 2. Asset Display
        asset_group = QGroupBox("Account Assets")
        asset_layout = QVBoxLayout()
        self.lbl_total_asset = QLabel("Total Asset: --")
        self.lbl_cash = QLabel("Cash: --")
        self.lbl_market_val = QLabel("Market Value: --")

        asset_layout.addWidget(self.lbl_total_asset)
        asset_layout.addWidget(self.lbl_cash)
        asset_layout.addWidget(self.lbl_market_val)
        asset_group.setLayout(asset_layout)

        left_panel.addWidget(control_group)
        left_panel.addWidget(asset_group)
        left_panel.addStretch()

        # Right Panel (Logs & Data)
        right_panel = QVBoxLayout()

        # 3. Log Window
        log_group = QGroupBox("System Logs")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)

        # 4. Signal/Position Table (Placeholder)
        table_group = QGroupBox("Active Positions / Signals")
        table_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Code", "Signal/Pos", "Price", "Time"])
        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)

        right_panel.addWidget(table_group, 1)
        right_panel.addWidget(log_group, 1)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 3)

        # Status Bar
        self.statusBar().showMessage("System Ready")

        # Internal State
        self.worker = None

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def start_system(self):
        self.log("Starting system...")
        self.statusBar().showMessage("System Running")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        # TODO: Init Worker
        # self.worker = WorkerThread(None)
        # self.worker.log_signal.connect(self.log)
        # self.worker.start()

    def stop_system(self):
        self.log("Stopping system...")
        self.statusBar().showMessage("System Stopped")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        if self.worker:
            self.worker.stop()
            self.worker.wait()

    def force_run(self):
        self.log("Manually triggering strategy run...")
        # TODO: Call backend logic


def launch_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
