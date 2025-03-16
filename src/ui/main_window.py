from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QTimer
from .control_panel import ControlPanel
from .visualization_panel import VisualizationPanel
from .metrics_panel import MetricsPanel
from src.rl_agent import TrafficRLAgent

class MainWindow(QMainWindow):
    def __init__(self, simulation_interface):
        super().__init__()
        self.simulation_interface = simulation_interface
        self.rl_agent = TrafficRLAgent(simulation_interface)
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface components"""
        # Set window properties
        self.setWindowTitle('Traffic Control Dashboard')
        self.setGeometry(100, 100, 1200, 800)  # Start with reasonable size
        self.setMinimumSize(1000, 600)  # Set minimum size to ensure content is visible
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)  # Add some spacing between panels
        main_layout.setContentsMargins(10, 10, 10, 10)  # Add margins around panels
        
        # Create and add panels
        # 1. Control Panel - Left side
        self.control_panel = ControlPanel()
        self.control_panel.setMinimumWidth(250)
        main_layout.addWidget(self.control_panel)
        
        # 2. Visualization Panel - Middle
        self.visualization_panel = VisualizationPanel()
        self.visualization_panel.setMinimumWidth(400)
        main_layout.addWidget(self.visualization_panel)
        
        # 3. Metrics Panel - Right side
        self.metrics_panel = MetricsPanel()
        self.metrics_panel.setMinimumWidth(300)
        main_layout.addWidget(self.metrics_panel)
        
        # Set stretch factors to control relative sizes
        main_layout.setStretchFactor(self.control_panel, 1)
        main_layout.setStretchFactor(self.visualization_panel, 2)
        main_layout.setStretchFactor(self.metrics_panel, 1)
        
        # Connect signals
        self.control_panel.learning_rate_changed.connect(self.update_learning_rate)
        self.control_panel.batch_size_changed.connect(self.update_batch_size)
        self.control_panel.n_steps_changed.connect(self.update_n_steps)
        self.control_panel.gamma_changed.connect(self.update_gamma)
        self.control_panel.traffic_mode_changed.connect(self.update_traffic_mode)
        self.control_panel.simulation_mode_changed.connect(self.update_simulation_mode)
        self.control_panel.speed_changed.connect(self.update_simulation_speed)
        self.control_panel.training_steps_changed.connect(self.update_training_steps)
        
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
        
        # Create timer for updating UI with simulation stats
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_simulation_display)
        self.update_timer.start(100)  # Update every 100ms
        
        # Note: We don't call show() or raise_() here because it's handled in main.py
        # This allows the window to be shown at the appropriate time
        
    def update_simulation_display(self):
        """Update UI elements with current simulation state"""
        if self.simulation_interface:
            # Update statistics
            waiting_count = sum(1 for v in self.simulation_interface.active_vehicles if v.state == "waiting")
            moving_count = sum(1 for v in self.simulation_interface.active_vehicles if v.state == "moving")
            arrived_count = len(self.simulation_interface.removed_vehicles)
            avg_satisfaction = self.simulation_interface.get_avg_satisfaction()
            episode = getattr(self.simulation_interface.data_recorder, 'current_episode', 0) if hasattr(self.simulation_interface, 'data_recorder') else 0
            tick = self.simulation_interface.current_tick
            
            # Update control panel stats
            self.control_panel.update_stats(waiting_count, moving_count, arrived_count, avg_satisfaction, episode, tick)
            
            # Update light states
            self.control_panel.update_light_states(self.simulation_interface.ns_light, self.simulation_interface.ew_light)
            
            # Update metrics using simulation interface methods
            metrics_data = self.simulation_interface.get_metrics()
            self.metrics_panel.update_metrics(metrics_data)
            
            # Update tutorial message if in tutorial mode
            if self.simulation_interface.tutorial_mode and self.simulation_interface.tutorial_step < len(self.simulation_interface.tutorial_messages):
                message = self.simulation_interface.tutorial_messages[self.simulation_interface.tutorial_step]
                self.control_panel.set_status_message(message)
            # Update episode state message if needed
            elif self.simulation_interface.episode_ended:
                self.control_panel.set_status_message("Episode Ended - Press N to start new episode")
            # Update training progress message if needed
            elif self.simulation_interface.training_in_progress:
                self.control_panel.set_status_message(f"Training in progress: {self.simulation_interface.current_training_steps} steps")
            else:
                self.control_panel.set_status_message("")
        
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
            self.control_panel.gamma_spin,
            self.control_panel.training_steps_slider
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
        
    def update_simulation_speed(self, value):
        """Update the simulation speed (FPS)"""
        if self.simulation_interface:
            self.simulation_interface.current_fps = value
    
    def update_training_steps(self, value):
        """Update the number of training steps"""
        if self.simulation_interface:
            self.simulation_interface.current_training_steps = value
            self.rl_agent.total_timesteps = value
        
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

    def calculate_avg_wait_time(self):
        """Calculate average wait time for vehicles at intersections"""
        return self.simulation_interface.get_avg_wait_time()

    def calculate_traffic_flow(self):
        """Calculate traffic flow rate (vehicles per minute)"""
        return self.simulation_interface.get_traffic_flow()

    def calculate_queue_length(self):
        """Calculate current queue length at intersections"""
        return self.simulation_interface.get_queue_length()

    def calculate_vehicle_density(self):
        """Calculate vehicle density (vehicles per lane)"""
        return self.simulation_interface.get_vehicle_density()

    def calculate_avg_speed(self):
        """Calculate average vehicle speed"""
        return self.simulation_interface.get_avg_speed()

    def calculate_stops_per_vehicle(self):
        """Calculate average number of stops per vehicle"""
        return self.simulation_interface.get_stops_per_vehicle()

    def calculate_fuel_efficiency(self):
        """Calculate fuel efficiency based on acceleration/deceleration patterns"""
        return self.simulation_interface.get_fuel_efficiency() 