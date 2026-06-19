import os
import pandas as pd
import random
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, 
                             QLabel, QLineEdit, QCheckBox, QProgressBar, QMessageBox, QGroupBox, QHeaderView, QSpinBox)
from PySide6.QtCore import Qt, QThreadPool, QRunnable, Slot, Signal, QObject
from app.generator import SyntheticFileGenerator
from app.engine import DeploymentEngine
from app.reporter import SOCReporter

class WorkerSignals(QObject):
    progress = Signal(dict)
    finished = Signal()

class EngineWorker(QRunnable):
    def __init__(self, host_row, source_files, target_paths, user, pwd):
        super().__init__()
        self.signals = WorkerSignals()
        self.host_row = host_row
        self.source_files = source_files
        self.target_paths = target_paths
        self.user = user
        self.pwd = pwd
        self.engine = DeploymentEngine()

    @Slot()
    def run(self):
        try:
            for s_file in self.source_files:
                for t_path in self.target_paths:
                    res = self.engine.deploy_to_endpoint(self.host_row, s_file, t_path, self.user, self.pwd)
                    self.signals.progress.emit(res)
        except Exception as e:
            print(f"Worker exception: {e}")
        finally:
            self.signals.finished.emit()

class SOCDeployerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SOC Ransomware Resilience Deployment Console")
        self.resize(1100, 850)
        self.selected_sources = []
        self.endpoints = []
        self.target_paths = []
        self.thread_pool = QThreadPool.globalInstance()
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 1. Source Layout
        src_box = QGroupBox("Source Files Staging Configuration")
        src_layout = QVBoxLayout(src_box)
        btn_layout = QHBoxLayout()
        self.btn_select_src = QPushButton("Select Source Files Manually")
        self.btn_select_src.clicked.connect(self.browse_sources)
        self.btn_load_src_excel = QPushButton("Load Source Files from Excel")
        self.btn_load_src_excel.setStyleSheet("background-color: #27ae60; color: white;")
        self.btn_load_src_excel.clicked.connect(self.load_source_excel)
        btn_layout.addWidget(self.btn_select_src)
        btn_layout.addWidget(self.btn_load_src_excel)
        
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel("Deployment File Count Limit:"))
        self.spin_file_limit = QSpinBox()
        self.spin_file_limit.setRange(1, 1000)
        self.spin_file_limit.setValue(2)
        limit_layout.addWidget(self.spin_file_limit)
        limit_layout.addStretch()
        self.lbl_src_status = QLabel("0 source files currently staged in memory.")
        src_layout.addLayout(btn_layout)
        src_layout.addLayout(limit_layout)
        src_layout.addWidget(self.lbl_src_status)
        layout.addWidget(src_box)

        # 2. Inventory layout
        inv_box = QGroupBox("Endpoint Fleet Targeting Inventory")
        inv_layout = QVBoxLayout(inv_box)
        self.btn_load_inv = QPushButton("Load Endpoint Inventory (Excel)")
        self.btn_load_inv.clicked.connect(self.load_inventory)
        self.table_hosts = QTableWidget(0, 5)
        self.table_hosts.setHorizontalHeaderLabels(["Select", "Hostname", "IP Address", "Domain", "Method"])
        inv_layout.addWidget(self.btn_load_inv)
        inv_layout.addWidget(self.table_hosts)
        layout.addWidget(inv_box)
        self.table_hosts.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # 3. Path Intelligence configuration
        path_box = QGroupBox("Malware Target Directory Patterns")
        path_layout = QVBoxLayout(path_box)
        self.btn_load_paths = QPushButton("Load Behavioral Strategies")
        self.btn_load_paths.clicked.connect(self.load_paths)
        self.table_paths = QTableWidget(0, 3)
        self.table_paths.setHorizontalHeaderLabels(["Select", "Target Directory Pattern", "Priority"])
        path_layout.addWidget(self.btn_load_paths)
        path_layout.addWidget(self.table_paths)
        layout.addWidget(path_box)
        self.table_paths.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # 4. Remote Domain/Local Credentials Context
        cred_box = QGroupBox("Administrative Enterprise Credentials Context")
        cred_layout = QHBoxLayout(cred_box)
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Domain\\Administrator")
        self.txt_pwd = QLineEdit()
        self.txt_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pwd.setPlaceholderText("Password")
        cred_layout.addWidget(QLabel("User Principal:"))
        cred_layout.addWidget(self.txt_user)
        cred_layout.addWidget(QLabel("Secret Key:"))
        cred_layout.addWidget(self.txt_pwd)
        layout.addWidget(cred_box)

        # 5. SIEM Ingestion Server API Config
        soc_box = QGroupBox("SOC Server API Log Forwarding Receiver")
        soc_layout = QHBoxLayout(soc_box)
        self.txt_soc_url = QLineEdit()
        self.txt_soc_url.setPlaceholderText("http://192.168.1.50:8080/api/logs")
        soc_layout.addWidget(QLabel("Ingestion Collector URL:"))
        soc_layout.addWidget(self.txt_soc_url)
        layout.addWidget(soc_box)

        # 6. Execution orchestration
        exec_box = QGroupBox("Deployment Execution Monitoring Engine")
        exec_layout = QVBoxLayout(exec_box)
        self.progress_bar = QProgressBar()
        self.btn_start = QPushButton("Start Orchestrated Deployment Run")
        self.btn_start.setStyleSheet("background-color: #1a5276; color: white; font-weight: bold;")
        self.btn_start.clicked.connect(self.start_deployment)
        exec_layout.addWidget(self.progress_bar)
        exec_layout.addWidget(self.btn_start)
        layout.addWidget(exec_box)

    def browse_sources(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Assets")
        if files:
            self.selected_sources = files
            self.lbl_src_status.setText(f"{len(files)} manual files staged.")

    def load_source_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Source Paths File", "", "Excel (*.xlsx)")
        if path:
            try:
                df = pd.read_excel(path)
                if 'Source File Path' in df.columns:
                    raw_paths = df['Source File Path'].dropna().astype(str).tolist()
                    valid_paths = [p for p in raw_paths if os.path.exists(p)]
                    self.selected_sources = valid_paths
                    self.lbl_src_status.setText(f"Loaded {len(valid_paths)} files from Excel.")
                else:
                    QMessageBox.critical(self, "Format Error", "Missing 'Source File Path' column.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def load_inventory(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Inventory File", "", "Excel (*.xlsx)")
        if path:
            df = pd.read_excel(path)
            self.table_hosts.setRowCount(len(df))
            self.endpoints = df.to_dict(orient='records')
            for idx, row in df.iterrows():
                chk = QCheckBox()
                chk.setChecked(True)
                self.table_hosts.setCellWidget(idx, 0, chk)
                self.table_hosts.setItem(idx, 1, QTableWidgetItem(str(row['Hostname'])))
                self.table_hosts.setItem(idx, 2, QTableWidgetItem(str(row['IP Address'])))
                self.table_hosts.setItem(idx, 3, QTableWidgetItem(str(row['Domain'])))
                self.table_hosts.setItem(idx, 4, QTableWidgetItem(str(row['Deployment Method'])))

    def load_paths(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Target Strategy File", "", "Excel (*.xlsx)")
        if path:
            df = pd.read_excel(path)
            self.table_paths.setRowCount(len(df))
            self.target_paths = df['Target Directory Pattern'].tolist()
            for idx, row in df.iterrows():
                chk = QCheckBox()
                chk.setChecked(True)
                self.table_paths.setCellWidget(idx, 0, chk)
                self.table_paths.setItem(idx, 1, QTableWidgetItem(str(row['Target Directory Pattern'])))
                self.table_paths.setItem(idx, 2, QTableWidgetItem(str(row['Priority'])))

    def start_deployment(self):
        active_paths = []
        for i in range(self.table_paths.rowCount()):
            if self.table_paths.cellWidget(i, 0).isChecked():
                active_paths.append(self.table_paths.item(i, 1).text())
                
        selected_hosts = []
        for i in range(self.table_hosts.rowCount()):
            if self.table_hosts.cellWidget(i, 0).isChecked():
                selected_hosts.append(self.endpoints[i])

        if not selected_hosts or not active_paths:
            QMessageBox.warning(self, "Scope Error", "Verify Inventory and Paths elements are loaded.")
            return

        deployment_pool = []
        requested_count = self.spin_file_limit.value()

        if self.selected_sources:
            if len(self.selected_sources) > requested_count:
                deployment_pool = random.sample(self.selected_sources, requested_count)
            else:
                deployment_pool = self.selected_sources
        else:
            synthetic_dir = os.path.join(os.getcwd(), "synthetic_staging")
            os.makedirs(synthetic_dir, exist_ok=True)
            for _ in range(requested_count):
                category = random.choice(["Finance", "Human Resources", "Business", "Engineering"])
                deployment_pool.append(SyntheticFileGenerator.create_synthetic_file(category, synthetic_dir))
            self.selected_sources = deployment_pool

        total_tasks = len(selected_hosts) * len(deployment_pool) * len(active_paths)
        self.progress_bar.setMaximum(total_tasks)
        self.progress_bar.setValue(0)
        
        user = self.txt_user.text()
        pwd = self.txt_pwd.text()

        for host in selected_hosts:
            worker = EngineWorker(host, deployment_pool, active_paths, user, pwd)
            worker.signals.progress.connect(self.handle_worker_progress)
            worker.signals.finished.connect(self.handle_worker_finished)
            self.thread_pool.start(worker)

    def handle_worker_progress(self, result):
        val = self.progress_bar.value()
        self.progress_bar.setValue(val + 1)

    def handle_worker_finished(self):
        if self.progress_bar.value() == self.progress_bar.maximum():
            soc_url = self.txt_soc_url.text().strip()
            # Triggers both local compilation and API forwarding
            SOCReporter().generate_consolidated_reports(soc_url=soc_url if soc_url else None)
            QMessageBox.information(self, "Run Complete", "All operations successfully executed and transmitted to SOC.")