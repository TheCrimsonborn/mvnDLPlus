import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QCheckBox, 
                               QProgressBar, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QIcon

from src.core.downloader import Downloader

class DownloadThread(QThread):
    progress_updated = Signal(int)
    finished_success = Signal(str)
    finished_error = Signal(str)

    def __init__(self, url, version, output_dir, ssl_verify):
        super().__init__()
        self.url = url
        self.version = version
        self.output_dir = output_dir
        self.ssl_verify = ssl_verify
        self.downloader = Downloader()

    def run(self):
        try:
            result_path = self.downloader.download_and_zip(
                self.url, 
                self.version, 
                self.output_dir, 
                self.ssl_verify, 
                self.progress_callback
            )
            self.finished_success.emit(result_path)
        except Exception as e:
            self.finished_error.emit(str(e))

    def progress_callback(self, percent):
        self.progress_updated.emit(percent)

    def cancel(self):
        self.downloader.cancel()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("mvnDLPlus")
        self.resize(600, 400)
        
        # Load Stylesheet
        try:
            with open(os.path.join(os.path.dirname(__file__), "styles.qss"), "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: styles.qss not found.")

        self.setup_ui()
        self.download_thread = None

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title_label = QLabel("mvnDLPlus")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Inputs
        input_layout = QVBoxLayout()
        input_layout.setSpacing(10)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste Link Here...")
        input_layout.addWidget(self.url_input)
        
        # self.version_input = QLineEdit()
        # self.version_input.setPlaceholderText("Version (e.g., 1.0.0) [Optional]")
        # input_layout.addWidget(self.version_input)
        
        layout.addLayout(input_layout)

        # Options
        options_layout = QHBoxLayout()
        self.ssl_checkbox = QCheckBox("Bypass SSL Verification")
        options_layout.addWidget(self.ssl_checkbox)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()
        self.download_btn = QPushButton("Download Package")
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()

    def start_download(self):
        raw_url = self.url_input.text().strip()
        
        if not raw_url:
            QMessageBox.warning(self, "Input Error", "Please enter a valid URL.")
            return

        # Parse URL
        targets, version = self.parse_url(raw_url)
        if not targets:
             QMessageBox.warning(self, "Input Error", "Could not parse the provided URL.")
             return

        # Auto-set save location (downloads folder next to main.py)
        # We assume main.py is in the parent directory of src/ui
        # But safer to use the current working directory or sys.argv[0]
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        output_dir = os.path.join(base_dir, "downloads")
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Could not create downloads directory:\n{e}")
                return

        self.toggle_ui(False)
        self.status_label.setText(f"Downloading {version if version else 'package'}...")
        self.progress_bar.setValue(0)
        
        ssl_verify = not self.ssl_checkbox.isChecked() 
        
        self.download_thread = DownloadThread(targets, version, output_dir, ssl_verify)
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.finished_success.connect(self.download_finished)
        self.download_thread.finished_error.connect(self.download_error)
        self.download_thread.start()

    def parse_url(self, raw_url):
        """
        Parses the input URL. 
        Returns a list of tuples: [(url, filename), ...]
        """
        try:
            if "mvnrepository.com/artifact/" in raw_url:
                # Format: https://mvnrepository.com/artifact/{group}/{artifact}/{version}
                parts = raw_url.split("mvnrepository.com/artifact/")[-1].split("/")
                if len(parts) >= 3:
                    group = parts[0]
                    artifact = parts[1]
                    version = parts[2]
                    
                    group_slashed = group.replace(".", "/")
                    base_url = f"https://repo1.maven.org/maven2/{group_slashed}/{artifact}/{version}/{artifact}-{version}"
                    
                    jar_url = f"{base_url}.jar"
                    jar_name = f"{artifact}-{version}.jar"
                    
                    pom_url = f"{base_url}.pom"
                    pom_name = f"{artifact}-{version}.pom"
                    
                    return [(jar_url, jar_name), (pom_url, pom_name)], version
            
            # Fallback
            filename = raw_url.split("/")[-1]
            return [(raw_url, filename)], None
        except Exception as e:
            print(f"Error parsing URL: {e}")
            return [], None

    def update_progress(self, percent):
        self.progress_bar.setValue(percent)

    def download_finished(self, path):
        self.toggle_ui(True)
        self.status_label.setText("Download Complete!")
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Success", f"Package saved to:\n{path}")

    def download_error(self, error_msg):
        self.toggle_ui(True)
        self.status_label.setText("Error occurred.")
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "Download Error", f"An error occurred:\n{error_msg}")

    def toggle_ui(self, enabled):
        self.url_input.setEnabled(enabled)
        # self.version_input.setEnabled(enabled)
        self.ssl_checkbox.setEnabled(enabled)
        self.download_btn.setEnabled(enabled)
        if enabled:
            self.download_btn.setText("Download Package")
        else:
            self.download_btn.setText("Downloading...")
