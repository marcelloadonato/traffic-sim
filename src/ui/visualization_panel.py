from PyQt5.QtWidgets import QWidget, QVBoxLayout
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

class VisualizationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create figure with subplots
        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 10))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Initialize data storage
        self.traffic_data = {
            'north': [],
            'south': [],
            'east': [],
            'west': []
        }
        self.reward_history = []
        self.steps = []
        
        self.setLayout(layout)
        
    def update_traffic_plot(self, traffic_counts):
        """Update the traffic pattern visualization"""
        self.ax1.clear()
        
        # Plot traffic counts for each direction
        for direction, counts in traffic_counts.items():
            self.ax1.plot(counts, label=direction.capitalize())
            
        self.ax1.set_title('Traffic Flow by Direction')
        self.ax1.set_xlabel('Time Steps')
        self.ax1.set_ylabel('Number of Vehicles')
        self.ax1.legend()
        self.ax1.grid(True)
        
        self.canvas.draw()
        
    def update_reward_plot(self, step, reward):
        """Update the reward history visualization"""
        self.steps.append(step)
        self.reward_history.append(reward)
        
        self.ax2.clear()
        self.ax2.plot(self.steps, self.reward_history)
        self.ax2.set_title('Agent Performance')
        self.ax2.set_xlabel('Time Steps')
        self.ax2.set_ylabel('Reward')
        self.ax2.grid(True)
        
        self.canvas.draw()
        
    def clear_plots(self):
        """Clear all visualization data"""
        self.traffic_data = {direction: [] for direction in self.traffic_data}
        self.reward_history = []
        self.steps = []
        self.ax1.clear()
        self.ax2.clear()
        self.canvas.draw() 