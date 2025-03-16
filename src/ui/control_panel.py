from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QSlider, QSpinBox, QDoubleSpinBox, QComboBox, 
                           QGroupBox, QPushButton, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, pyqtSignal

class ControlPanel(QWidget):
    # Signals for parameter changes
    learning_rate_changed = pyqtSignal(float)
    batch_size_changed = pyqtSignal(int)
    n_steps_changed = pyqtSignal(int)
    gamma_changed = pyqtSignal(float)
    traffic_mode_changed = pyqtSignal(str)
    simulation_mode_changed = pyqtSignal(str)  # New signal for simulation mode
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Simulation Mode Group
        mode_group = QGroupBox("Simulation Mode")
        mode_layout = QVBoxLayout()
        
        # Create radio buttons for different modes
        self.rl_mode = QRadioButton("Reinforcement Learning")
        self.manual_mode = QRadioButton("Manual Control")
        self.tutorial_mode = QRadioButton("Tutorial Mode")
        
        # Set RL mode as default
        self.rl_mode.setChecked(True)
        
        # Create button group
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.rl_mode)
        self.mode_group.addButton(self.manual_mode)
        self.mode_group.addButton(self.tutorial_mode)
        
        # Connect mode changes to signal
        self.mode_group.buttonClicked.connect(self.on_mode_changed)
        
        # Add radio buttons to layout
        mode_layout.addWidget(self.rl_mode)
        mode_layout.addWidget(self.manual_mode)
        mode_layout.addWidget(self.tutorial_mode)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # RL Agent Parameters Group
        rl_group = QGroupBox("RL Agent Parameters")
        rl_layout = QVBoxLayout()
        
        # Learning Rate Control
        lr_layout = QHBoxLayout()
        lr_label = QLabel("Learning Rate:")
        self.lr_spin = QDoubleSpinBox()
        self.lr_spin.setRange(0.0001, 0.01)
        self.lr_spin.setValue(0.0003)
        self.lr_spin.setSingleStep(0.0001)
        self.lr_spin.valueChanged.connect(self.learning_rate_changed.emit)
        lr_layout.addWidget(lr_label)
        lr_layout.addWidget(self.lr_spin)
        rl_layout.addLayout(lr_layout)
        
        # Batch Size Control
        batch_layout = QHBoxLayout()
        batch_label = QLabel("Batch Size:")
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(32, 256)
        self.batch_spin.setValue(64)
        self.batch_spin.valueChanged.connect(self.batch_size_changed.emit)
        batch_layout.addWidget(batch_label)
        batch_layout.addWidget(self.batch_spin)
        rl_layout.addLayout(batch_layout)
        
        # N Steps Control
        steps_layout = QHBoxLayout()
        steps_label = QLabel("Steps per Update:")
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(512, 4096)
        self.steps_spin.setValue(2048)
        self.steps_spin.valueChanged.connect(self.n_steps_changed.emit)
        steps_layout.addWidget(steps_label)
        steps_layout.addWidget(self.steps_spin)
        rl_layout.addLayout(steps_layout)
        
        # Gamma Control
        gamma_layout = QHBoxLayout()
        gamma_label = QLabel("Discount Factor (Gamma):")
        self.gamma_spin = QDoubleSpinBox()
        self.gamma_spin.setRange(0.9, 0.999)
        self.gamma_spin.setValue(0.99)
        self.gamma_spin.setSingleStep(0.001)
        self.gamma_spin.valueChanged.connect(self.gamma_changed.emit)
        gamma_layout.addWidget(gamma_label)
        gamma_layout.addWidget(self.gamma_spin)
        rl_layout.addLayout(gamma_layout)
        
        rl_group.setLayout(rl_layout)
        layout.addWidget(rl_group)
        
        # Traffic Generation Group
        traffic_group = QGroupBox("Traffic Generation")
        traffic_layout = QVBoxLayout()
        
        # Traffic Mode Selection
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Traffic Mode:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Random", "Pattern", "Peak Hours"])
        self.mode_combo.currentTextChanged.connect(self.traffic_mode_changed.emit)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        traffic_layout.addLayout(mode_layout)
        
        traffic_group.setLayout(traffic_layout)
        layout.addWidget(traffic_group)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Training")
        self.stop_button = QPushButton("Stop Training")
        self.reset_button = QPushButton("Reset")
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.reset_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def on_mode_changed(self, button):
        """Handle simulation mode changes"""
        if button == self.rl_mode:
            self.simulation_mode_changed.emit("RL")
        elif button == self.manual_mode:
            self.simulation_mode_changed.emit("Manual")
        else:  # tutorial mode
            self.simulation_mode_changed.emit("Tutorial")
            
    def get_rl_parameters(self):
        """Get current RL agent parameters"""
        return {
            'learning_rate': self.lr_spin.value(),
            'batch_size': self.batch_spin.value(),
            'n_steps': self.steps_spin.value(),
            'gamma': self.gamma_spin.value()
        }
        
    def get_traffic_mode(self):
        """Get current traffic generation mode"""
        return self.mode_combo.currentText()
        
    def get_simulation_mode(self):
        """Get current simulation mode"""
        if self.rl_mode.isChecked():
            return "RL"
        elif self.manual_mode.isChecked():
            return "Manual"
        else:
            return "Tutorial"
            
    def set_simulation_mode(self, mode):
        """Set the simulation mode"""
        if mode == "RL":
            self.rl_mode.setChecked(True)
        elif mode == "Manual":
            self.manual_mode.setChecked(True)
        else:
            self.tutorial_mode.setChecked(True) 