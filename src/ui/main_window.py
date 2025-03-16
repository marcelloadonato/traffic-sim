from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QMessageBox
from .control_panel import ControlPanel
from .visualization_panel import VisualizationPanel
from src.rl_agent import TrafficRLAgent

class MainWindow(QMainWindow):
    def __init__(self, simulation_interface):
        super().__init__()
        self.simulation_interface = simulation_interface
        self.rl_agent = TrafficRLAgent(simulation_interface)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Traffic Light Control System')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Create and add control panel
        self.control_panel = ControlPanel()
        layout.addWidget(self.control_panel)
        
        # Create and add visualization panel
        self.visualization_panel = VisualizationPanel()
        layout.addWidget(self.visualization_panel)
        
        # Connect signals
        self.control_panel.learning_rate_changed.connect(self.update_learning_rate)
        self.control_panel.batch_size_changed.connect(self.update_batch_size)
        self.control_panel.n_steps_changed.connect(self.update_n_steps)
        self.control_panel.gamma_changed.connect(self.update_gamma)
        self.control_panel.traffic_mode_changed.connect(self.update_traffic_mode)
        self.control_panel.simulation_mode_changed.connect(self.update_simulation_mode)
        
        self.control_panel.start_button.clicked.connect(self.start_training)
        self.control_panel.stop_button.clicked.connect(self.stop_training)
        self.control_panel.reset_button.clicked.connect(self.reset_simulation)
        
        # Connect RL agent signals to visualization panel
        if hasattr(self.simulation_interface, 'data_recorder'):
            self.simulation_interface.data_recorder.traffic_update.connect(
                self.visualization_panel.update_traffic_plot
            )
            self.simulation_interface.data_recorder.reward_update.connect(
                self.visualization_panel.update_reward_plot
            )
        
        # Set initial button states
        self.update_button_states()
        
    def update_button_states(self):
        """Update button states based on training status and simulation mode"""
        is_training = self.simulation_interface.training_in_progress
        current_mode = self.control_panel.get_simulation_mode()
        
        # Only enable RL controls in RL mode
        self.control_panel.start_button.setEnabled(not is_training and current_mode == "RL")
        self.control_panel.stop_button.setEnabled(is_training and current_mode == "RL")
        self.control_panel.reset_button.setEnabled(not is_training)
        
        # Enable/disable RL parameter controls based on mode
        rl_controls = [
            self.control_panel.lr_spin,
            self.control_panel.batch_spin,
            self.control_panel.steps_spin,
            self.control_panel.gamma_spin
        ]
        for control in rl_controls:
            control.setEnabled(current_mode == "RL")
        
    def update_learning_rate(self, value):
        """Update the learning rate of the RL agent"""
        self.rl_agent.model.learning_rate = value
        
    def update_batch_size(self, value):
        """Update the batch size of the RL agent"""
        self.rl_agent.model.batch_size = value
        
    def update_n_steps(self, value):
        """Update the number of steps per update"""
        self.rl_agent.model.n_steps = value
        
    def update_gamma(self, value):
        """Update the discount factor"""
        self.rl_agent.model.gamma = value
        
    def update_traffic_mode(self, mode):
        """Update the traffic generation mode"""
        self.simulation_interface.set_traffic_mode(mode)
        
    def update_simulation_mode(self, mode):
        """Update the simulation mode"""
        try:
            # Stop any ongoing training
            if self.simulation_interface.training_in_progress:
                self.simulation_interface.rl_agent.stop_training()
            
            # Reset the simulation
            self.simulation_interface.reset()
            
            # Clear visualizations
            self.visualization_panel.clear_plots()
            
            # Set the new mode
            self.simulation_interface.set_mode(mode)
            
            # Update button states
            self.update_button_states()
            
            # Show mode-specific message
            if mode == "Tutorial":
                QMessageBox.information(self, "Tutorial Mode", 
                    "Welcome to Tutorial Mode!\n\n"
                    "This mode will guide you through the traffic simulation system.\n"
                    "Press C to advance through the tutorial steps.")
            elif mode == "Manual":
                QMessageBox.information(self, "Manual Mode", 
                    "Welcome to Manual Mode!\n\n"
                    "You can control the traffic lights using the SPACE bar.\n"
                    "Press SPACE to toggle between NS and EW green lights.")
            else:  # RL Mode
                QMessageBox.information(self, "RL Mode", 
                    "Welcome to RL Mode!\n\n"
                    "The AI agent will control the traffic lights.\n"
                    "Use the controls to adjust training parameters.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update simulation mode: {str(e)}")
            print(f"Error updating simulation mode: {e}")
            import traceback
            traceback.print_exc()
        
    def start_training(self):
        """Start the RL agent training"""
        try:
            # Reset the environment
            self.simulation_interface.reset()
            
            # Clear previous visualizations
            self.visualization_panel.clear_plots()
            
            # Start training
            self.rl_agent.train()
            self.update_button_states()
        except Exception as e:
            QMessageBox.critical(self, "Training Error", f"Failed to start training: {str(e)}")
            self.update_button_states()
        
    def stop_training(self):
        """Stop the RL agent training"""
        try:
            self.rl_agent.stop_training()
            self.update_button_states()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to stop training: {str(e)}")
        
    def reset_simulation(self):
        """Reset the simulation and visualization"""
        try:
            self.simulation_interface.reset()
            self.visualization_panel.clear_plots()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reset simulation: {str(e)}")
        
    def on_training_finished(self):
        """Handle training completion"""
        self.update_button_states()
        QMessageBox.information(self, "Training Complete", "The training process has completed successfully.")
        
    def on_training_error(self, error_msg):
        """Handle training errors"""
        self.update_button_states()
        QMessageBox.critical(self, "Training Error", f"An error occurred during training: {error_msg}") 