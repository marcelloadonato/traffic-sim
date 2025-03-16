from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QSlider, QSpinBox, QDoubleSpinBox, QComboBox, 
                           QGroupBox, QPushButton, QRadioButton, QButtonGroup,
                           QFrame, QLCDNumber, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class ControlPanel(QWidget):
    # Signals for parameter changes
    learning_rate_changed = pyqtSignal(float)
    batch_size_changed = pyqtSignal(int)
    n_steps_changed = pyqtSignal(int)
    gamma_changed = pyqtSignal(float)
    traffic_mode_changed = pyqtSignal(str)
    simulation_mode_changed = pyqtSignal(str)  # New signal for simulation mode
    speed_changed = pyqtSignal(int)  # New signal for simulation speed
    training_steps_changed = pyqtSignal(int)  # New signal for training steps
    
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
        
        # Add radio buttons and descriptions to layout
        mode_layout.addWidget(self.rl_mode)
        rl_desc = QLabel("AI agent learns optimal traffic light control through trial and error")
        rl_desc.setStyleSheet("color: #666; font-size: 10pt; margin-left: 20px;")
        mode_layout.addWidget(rl_desc)
        
        mode_layout.addWidget(self.manual_mode)
        manual_desc = QLabel("You control traffic lights manually using the SPACE bar")
        manual_desc.setStyleSheet("color: #666; font-size: 10pt; margin-left: 20px;")
        mode_layout.addWidget(manual_desc)
        
        mode_layout.addWidget(self.tutorial_mode)
        tutorial_desc = QLabel("Learn how the system works through guided steps")
        tutorial_desc.setStyleSheet("color: #666; font-size: 10pt; margin-left: 20px;")
        mode_layout.addWidget(tutorial_desc)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Simulation Speed Group
        speed_group = QGroupBox("Simulation Speed")
        speed_layout = QVBoxLayout()
        
        # Speed Slider
        speed_slider_layout = QHBoxLayout()
        speed_slider_label = QLabel("Speed (FPS):")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 60)
        self.speed_slider.setValue(30)
        self.speed_value_label = QLabel("30")
        
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        
        speed_slider_layout.addWidget(speed_slider_label)
        speed_slider_layout.addWidget(self.speed_slider)
        speed_slider_layout.addWidget(self.speed_value_label)
        speed_layout.addLayout(speed_slider_layout)
        
        speed_desc = QLabel("Adjust how fast the simulation runs (1-60 frames per second)")
        speed_desc.setStyleSheet("color: #666; font-size: 10pt;")
        speed_layout.addWidget(speed_desc)
        
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)
        
        # Simulation Stats Group
        stats_group = QGroupBox("Simulation Statistics")
        stats_layout = QGridLayout()
        
        # Add stat labels and values
        self.waiting_label = QLabel("Waiting:")
        self.waiting_value = QLabel("0")
        stats_layout.addWidget(self.waiting_label, 0, 0)
        stats_layout.addWidget(self.waiting_value, 0, 1)
        
        self.moving_label = QLabel("Moving:")
        self.moving_value = QLabel("0")
        stats_layout.addWidget(self.moving_label, 1, 0)
        stats_layout.addWidget(self.moving_value, 1, 1)
        
        self.arrived_label = QLabel("Arrived:")
        self.arrived_value = QLabel("0")
        stats_layout.addWidget(self.arrived_label, 2, 0)
        stats_layout.addWidget(self.arrived_value, 2, 1)
        
        self.satisfaction_label = QLabel("Satisfaction:")
        self.satisfaction_value = QLabel("0.0")
        stats_layout.addWidget(self.satisfaction_label, 3, 0)
        stats_layout.addWidget(self.satisfaction_value, 3, 1)
        
        self.episode_label = QLabel("Episode:")
        self.episode_value = QLabel("0")
        stats_layout.addWidget(self.episode_label, 4, 0)
        stats_layout.addWidget(self.episode_value, 4, 1)
        
        self.tick_label = QLabel("Tick:")
        self.tick_value = QLabel("0")
        stats_layout.addWidget(self.tick_label, 5, 0)
        stats_layout.addWidget(self.tick_value, 5, 1)
        
        # Add light state indicators
        self.ns_light_label = QLabel("NS Light:")
        self.ns_light_value = QLabel("Green")
        self.ns_light_value.setStyleSheet("background-color: green; color: white; padding: 2px;")
        stats_layout.addWidget(self.ns_light_label, 0, 2)
        stats_layout.addWidget(self.ns_light_value, 0, 3)
        
        self.ew_light_label = QLabel("EW Light:")
        self.ew_light_value = QLabel("Red")
        self.ew_light_value.setStyleSheet("background-color: red; color: white; padding: 2px;")
        stats_layout.addWidget(self.ew_light_label, 1, 2)
        stats_layout.addWidget(self.ew_light_value, 1, 3)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # RL Agent Parameters Group
        rl_group = QGroupBox("RL Agent Parameters")
        rl_layout = QVBoxLayout()
        
        # Learning Rate Control
        lr_layout = QHBoxLayout()
        lr_label = QLabel("Learning Rate:")
        lr_label.setToolTip("Controls how quickly the AI adjusts its strategy based on experience.\n"
                          "Higher values (e.g., 0.01) make learning faster but less stable.\n"
                          "Lower values (e.g., 0.0001) make learning slower but more stable.\n"
                          "Changes take effect on next episode.")
        self.lr_spin = QDoubleSpinBox()
        self.lr_spin.setRange(0.0001, 0.01)
        self.lr_spin.setValue(0.0003)
        self.lr_spin.setSingleStep(0.0001)
        self.lr_spin.setDecimals(4)  # Show 4 decimal places
        self.lr_spin.valueChanged.connect(self.learning_rate_changed.emit)
        self.lr_spin.setToolTip("Controls how quickly the AI adjusts its strategy based on experience.\n"
                              "Higher values (e.g., 0.01) make learning faster but less stable.\n"
                              "Lower values (e.g., 0.0001) make learning slower but more stable.\n"
                              "Changes take effect on next episode.")
        lr_layout.addWidget(lr_label)
        lr_layout.addWidget(self.lr_spin)
        rl_layout.addLayout(lr_layout)
        
        lr_desc = QLabel("How quickly the AI learns from its experiences (0.0001-0.01)")
        lr_desc.setStyleSheet("color: #666; font-size: 10pt;")
        rl_layout.addWidget(lr_desc)
        
        # Batch Size Control
        batch_layout = QHBoxLayout()
        batch_label = QLabel("Batch Size:")
        batch_label.setToolTip("Number of experiences the AI learns from in each update.\n"
                             "Larger batches (e.g., 256) provide more stable learning but require more memory.\n"
                             "Smaller batches (e.g., 32) make learning faster but less stable.\n"
                             "Changes take effect on next episode.")
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(32, 256)
        self.batch_spin.setValue(64)
        self.batch_spin.valueChanged.connect(self.batch_size_changed.emit)
        self.batch_spin.setToolTip("Number of experiences the AI learns from in each update.\n"
                                 "Larger batches (e.g., 256) provide more stable learning but require more memory.\n"
                                 "Smaller batches (e.g., 32) make learning faster but less stable.\n"
                                 "Changes take effect on next episode.")
        batch_layout.addWidget(batch_label)
        batch_layout.addWidget(self.batch_spin)
        rl_layout.addLayout(batch_layout)
        
        batch_desc = QLabel("Number of experiences the AI learns from at once (32-256)")
        batch_desc.setStyleSheet("color: #666; font-size: 10pt;")
        rl_layout.addWidget(batch_desc)
        
        # N Steps Control
        steps_layout = QHBoxLayout()
        steps_label = QLabel("Steps per Update:")
        steps_label.setToolTip("How often the AI updates its knowledge.\n"
                             "More steps (e.g., 4096) between updates provide better learning but slower progress.\n"
                             "Fewer steps (e.g., 512) make learning faster but potentially less stable.\n"
                             "Changes take effect on next episode.")
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(512, 4096)
        self.steps_spin.setValue(2048)
        self.steps_spin.valueChanged.connect(self.n_steps_changed.emit)
        self.steps_spin.setToolTip("How often the AI updates its knowledge.\n"
                                 "More steps (e.g., 4096) between updates provide better learning but slower progress.\n"
                                 "Fewer steps (e.g., 512) make learning faster but potentially less stable.\n"
                                 "Changes take effect on next episode.")
        steps_layout.addWidget(steps_label)
        steps_layout.addWidget(self.steps_spin)
        rl_layout.addLayout(steps_layout)
        
        steps_desc = QLabel("How often the AI updates its knowledge (512-4096 steps)")
        steps_desc.setStyleSheet("color: #666; font-size: 10pt;")
        rl_layout.addWidget(steps_desc)
        
        # Gamma Control
        gamma_layout = QHBoxLayout()
        gamma_label = QLabel("Discount Factor (Gamma):")
        gamma_label.setToolTip("How much the AI values future rewards vs immediate rewards.\n"
                             "Higher values (e.g., 0.999) make the AI plan further ahead.\n"
                             "Lower values (e.g., 0.9) make the AI focus on immediate rewards.\n"
                             "Changes take effect on next episode.")
        self.gamma_spin = QDoubleSpinBox()
        self.gamma_spin.setRange(0.9, 0.999)
        self.gamma_spin.setValue(0.99)
        self.gamma_spin.setSingleStep(0.001)
        self.gamma_spin.setDecimals(3)  # Show 3 decimal places
        self.gamma_spin.valueChanged.connect(self.gamma_changed.emit)
        self.gamma_spin.setToolTip("How much the AI values future rewards vs immediate rewards.\n"
                                 "Higher values (e.g., 0.999) make the AI plan further ahead.\n"
                                 "Lower values (e.g., 0.9) make the AI focus on immediate rewards.\n"
                                 "Changes take effect on next episode.")
        gamma_layout.addWidget(gamma_label)
        gamma_layout.addWidget(self.gamma_spin)
        rl_layout.addLayout(gamma_layout)
        
        gamma_desc = QLabel("How much the AI values future rewards vs immediate rewards (0.9-0.999)")
        gamma_desc.setStyleSheet("color: #666; font-size: 10pt;")
        rl_layout.addWidget(gamma_desc)
        
        # Training Steps Slider
        training_slider_layout = QHBoxLayout()
        training_slider_label = QLabel("Training Steps:")
        training_slider_label.setToolTip("Total number of steps the AI will train for.\n"
                                       "More steps allow for better learning but take longer.\n"
                                       "Fewer steps make training faster but may not reach optimal performance.\n"
                                       "Changes take effect when starting new training.")
        self.training_steps_slider = QSlider(Qt.Horizontal)
        self.training_steps_slider.setRange(100, 20000)
        self.training_steps_slider.setValue(2000)
        self.training_steps_value = QLabel("2000")
        self.training_steps_value.setToolTip("Total number of steps the AI will train for.\n"
                                           "More steps allow for better learning but take longer.\n"
                                           "Fewer steps make training faster but may not reach optimal performance.\n"
                                           "Changes take effect when starting new training.")
        
        self.training_steps_slider.valueChanged.connect(self.on_training_steps_changed)
        self.training_steps_slider.setToolTip("Total number of steps the AI will train for.\n"
                                            "More steps allow for better learning but take longer.\n"
                                            "Fewer steps make training faster but may not reach optimal performance.\n"
                                            "Changes take effect when starting new training.")
        
        training_slider_layout.addWidget(training_slider_label)
        training_slider_layout.addWidget(self.training_steps_slider)
        training_slider_layout.addWidget(self.training_steps_value)
        rl_layout.addLayout(training_slider_layout)
        
        training_desc = QLabel("Total number of steps the AI will train for (100-20000)")
        training_desc.setStyleSheet("color: #666; font-size: 10pt;")
        rl_layout.addWidget(training_desc)
        
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
        
        traffic_desc = QLabel("Choose how vehicles are generated:\n"
                            "• Random: Equal chance from all directions\n"
                            "• Pattern: Predictable traffic patterns\n"
                            "• Peak Hours: Simulated rush hour traffic")
        traffic_desc.setStyleSheet("color: #666; font-size: 10pt;")
        traffic_layout.addWidget(traffic_desc)
        
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
        
        # Status bar for tutorial messages or episode messages
        self.status_frame = QFrame()
        self.status_frame.setFrameShape(QFrame.StyledPanel)
        self.status_frame.setFrameShadow(QFrame.Sunken)
        status_layout = QVBoxLayout(self.status_frame)
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        layout.addWidget(self.status_frame)
        
        self.setLayout(layout)
        
    def on_mode_changed(self, button):
        """Handle simulation mode changes"""
        if button == self.rl_mode:
            self.simulation_mode_changed.emit("RL")
        elif button == self.manual_mode:
            self.simulation_mode_changed.emit("Manual")
        else:  # tutorial mode
            self.simulation_mode_changed.emit("Tutorial")
            
    def on_speed_changed(self, value):
        """Handle speed slider changes"""
        self.speed_value_label.setText(str(value))
        self.speed_changed.emit(value)
        
    def on_training_steps_changed(self, value):
        """Handle training steps slider changes"""
        self.training_steps_value.setText(str(value))
        self.training_steps_changed.emit(value)
            
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
            
    def update_stats(self, waiting_count, moving_count, arrived_count, avg_satisfaction, episode, tick):
        """Update the simulation statistics display"""
        self.waiting_value.setText(str(waiting_count))
        self.moving_value.setText(str(moving_count))
        self.arrived_value.setText(str(arrived_count))
        self.satisfaction_value.setText(f"{avg_satisfaction:.3f}")
        self.episode_value.setText(str(episode))
        self.tick_value.setText(str(tick))
        
    def update_light_states(self, ns_light, ew_light):
        """Update the traffic light state indicators"""
        # Update NS light
        self.ns_light_value.setText(ns_light.capitalize())
        if ns_light == "green":
            self.ns_light_value.setStyleSheet("background-color: green; color: white; padding: 2px;")
        elif ns_light == "yellow":
            self.ns_light_value.setStyleSheet("background-color: yellow; color: black; padding: 2px;")
        else:  # red
            self.ns_light_value.setStyleSheet("background-color: red; color: white; padding: 2px;")
            
        # Update EW light
        self.ew_light_value.setText(ew_light.capitalize())
        if ew_light == "green":
            self.ew_light_value.setStyleSheet("background-color: green; color: white; padding: 2px;")
        elif ew_light == "yellow":
            self.ew_light_value.setStyleSheet("background-color: yellow; color: black; padding: 2px;")
        else:  # red
            self.ew_light_value.setStyleSheet("background-color: red; color: white; padding: 2px;")
            
    def set_status_message(self, message):
        """Set the status/tutorial message"""
        self.status_label.setText(message) 