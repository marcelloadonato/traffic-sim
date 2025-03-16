from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QScrollArea, QPushButton, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor

class MetricsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Create scroll area for the entire panel
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create container widget for scroll area
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # Metrics Section
        metrics_group = QGroupBox("Traffic Metrics")
        metrics_layout = QVBoxLayout()
        
        # Create metric labels with styling
        self.metric_labels = {}
        metrics = [
            ("avg_wait_time", "Average Wait Time"),
            ("traffic_flow", "Traffic Flow (vehicles/min)"),
            ("queue_length", "Queue Length"),
            ("vehicle_density", "Vehicle Density"),
            ("avg_speed", "Average Speed"),
            ("stops_per_vehicle", "Stops per Vehicle"),
            ("fuel_efficiency", "Fuel Efficiency")
        ]
        
        for metric_id, metric_name in metrics:
            metric_frame = QFrame()
            metric_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
            metric_frame.setStyleSheet("QFrame { background-color: #f0f0f0; }")
            
            metric_layout = QHBoxLayout(metric_frame)
            
            name_label = QLabel(metric_name)
            name_label.setFont(QFont("Arial", 10))
            name_label.setWordWrap(True)
            
            value_label = QLabel("0")
            value_label.setFont(QFont("Arial", 10, QFont.Bold))
            value_label.setAlignment(Qt.AlignRight)
            value_label.setMinimumWidth(60)  # Ensure consistent width for values
            
            metric_layout.addWidget(name_label)
            metric_layout.addWidget(value_label)
            
            metrics_layout.addWidget(metric_frame)
            self.metric_labels[metric_id] = value_label
        
        metrics_group.setLayout(metrics_layout)
        container_layout.addWidget(metrics_group)
        
        # Educational Information Section
        edu_group = QGroupBox("Traffic Management Guide")
        edu_layout = QVBoxLayout()
        
        # Traffic Light Information
        light_info = QFrame()
        light_info.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        light_layout = QVBoxLayout(light_info)
        
        light_title = QLabel("Traffic Light States")
        light_title.setFont(QFont("Arial", 11, QFont.Bold))
        light_layout.addWidget(light_title)
        
        light_states = [
            ("Red", "Stop - Vehicles must wait at the intersection"),
            ("Yellow", "Caution - Clear the intersection"),
            ("Green", "Go - Vehicles can proceed through the intersection")
        ]
        
        for state, desc in light_states:
            state_frame = QFrame()
            state_layout = QVBoxLayout(state_frame)  # Changed to VBoxLayout for better text wrapping
            
            state_label = QLabel(state)
            state_label.setFont(QFont("Arial", 10, QFont.Bold))
            state_label.setStyleSheet(f"color: {state.lower()}")
            
            desc_label = QLabel(desc)
            desc_label.setFont(QFont("Arial", 10))
            desc_label.setWordWrap(True)  # Enable text wrapping
            
            state_layout.addWidget(state_label)
            state_layout.addWidget(desc_label)
            light_layout.addWidget(state_frame)
        
        edu_layout.addWidget(light_info)
        
        # Vehicle Behavior Information
        vehicle_info = QFrame()
        vehicle_info.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        vehicle_layout = QVBoxLayout(vehicle_info)
        
        vehicle_title = QLabel("Vehicle Behavior")
        vehicle_title.setFont(QFont("Arial", 11, QFont.Bold))
        vehicle_layout.addWidget(vehicle_title)
        
        behaviors = [
            ("Following Distance", "Vehicles maintain safe distance from vehicles ahead"),
            ("Speed Control", "Vehicles adjust speed based on traffic conditions"),
            ("Lane Changes", "Vehicles change lanes only when safe and necessary"),
            ("Intersection Rules", "Vehicles follow traffic light signals and yield to emergency vehicles")
        ]
        
        for behavior, desc in behaviors:
            behavior_frame = QFrame()
            behavior_layout = QVBoxLayout(behavior_frame)  # Changed to VBoxLayout
            
            behavior_label = QLabel(behavior)
            behavior_label.setFont(QFont("Arial", 10, QFont.Bold))
            
            desc_label = QLabel(desc)
            desc_label.setFont(QFont("Arial", 10))
            desc_label.setWordWrap(True)  # Enable text wrapping
            
            behavior_layout.addWidget(behavior_label)
            behavior_layout.addWidget(desc_label)
            vehicle_layout.addWidget(behavior_frame)
        
        edu_layout.addWidget(vehicle_info)
        
        # Best Practices Information
        practices_info = QFrame()
        practices_info.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        practices_layout = QVBoxLayout(practices_info)
        
        practices_title = QLabel("Traffic Management Best Practices")
        practices_title.setFont(QFont("Arial", 11, QFont.Bold))
        practices_layout.addWidget(practices_title)
        
        practices = [
            ("Optimal Timing", "Traffic lights are timed to minimize wait times"),
            ("Queue Management", "Intersections are managed to prevent queue buildup"),
            ("Flow Optimization", "Traffic flow is optimized for peak conditions"),
            ("Safety First", "Safety measures take precedence over speed")
        ]
        
        for practice, desc in practices:
            practice_frame = QFrame()
            practice_layout = QVBoxLayout(practice_frame)  # Changed to VBoxLayout
            
            practice_label = QLabel(practice)
            practice_label.setFont(QFont("Arial", 10, QFont.Bold))
            
            desc_label = QLabel(desc)
            desc_label.setFont(QFont("Arial", 10))
            desc_label.setWordWrap(True)  # Enable text wrapping
            
            practice_layout.addWidget(practice_label)
            practice_layout.addWidget(desc_label)
            practices_layout.addWidget(practice_frame)
        
        edu_layout.addWidget(practices_info)
        
        edu_group.setLayout(edu_layout)
        container_layout.addWidget(edu_group)
        
        # Add container to scroll area
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Set minimum width for the panel
        self.setMinimumWidth(300)
        
    def update_metrics(self, metrics_data):
        """Update the metrics display with new data"""
        for metric_id, value in metrics_data.items():
            if metric_id in self.metric_labels:
                # Format the value based on the metric type
                if metric_id == 'avg_wait_time':
                    formatted_value = f"{value:.1f}s"
                elif metric_id == 'traffic_flow':
                    formatted_value = f"{value:.1f}"
                elif metric_id == 'queue_length':
                    formatted_value = str(int(value))
                elif metric_id == 'vehicle_density':
                    formatted_value = f"{value:.1f}"
                elif metric_id == 'avg_speed':
                    formatted_value = f"{value:.1f}px/s"
                elif metric_id == 'stops_per_vehicle':
                    formatted_value = f"{value:.1f}"
                elif metric_id == 'fuel_efficiency':
                    formatted_value = f"{value:.1f}%"
                else:
                    formatted_value = str(value)
                
                self.metric_labels[metric_id].setText(formatted_value) 