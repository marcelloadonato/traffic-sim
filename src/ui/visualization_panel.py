from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
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
        plt.style.use('seaborn')  # Use a better style
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
        try:
            # Update data storage
            for direction, count in traffic_counts.items():
                self.traffic_data[direction].append(count)
            
            # Keep only last 100 points for better visualization
            max_points = 100
            for direction in self.traffic_data:
                self.traffic_data[direction] = self.traffic_data[direction][-max_points:]
            
            # Clear and redraw plot
            self.ax1.clear()
            
            # Plot traffic counts for each direction
            for direction, counts in self.traffic_data.items():
                if counts:  # Only plot if we have data
                    self.ax1.plot(counts, label=direction.capitalize())
            
            self.ax1.set_title('Traffic Flow by Direction')
            self.ax1.set_xlabel('Time Steps')
            self.ax1.set_ylabel('Number of Vehicles')
            self.ax1.legend()
            self.ax1.grid(True)
            
            # Force redraw
            self.canvas.draw_idle()
        except Exception as e:
            print(f"Error updating traffic plot: {e}")
            import traceback
            traceback.print_exc()
        
    def update_reward_plot(self, step, reward):
        """Update the reward history visualization"""
        try:
            # Update data storage
            self.steps.append(step)
            self.reward_history.append(reward)
            
            # Keep only last 100 points for better visualization
            max_points = 100
            self.steps = self.steps[-max_points:]
            self.reward_history = self.reward_history[-max_points:]
            
            # Clear and redraw plot
            self.ax2.clear()
            self.ax2.plot(self.steps, self.reward_history)
            self.ax2.set_title('Agent Performance')
            self.ax2.set_xlabel('Time Steps')
            self.ax2.set_ylabel('Reward')
            self.ax2.grid(True)
            
            # Force redraw
            self.canvas.draw_idle()
        except Exception as e:
            print(f"Error updating reward plot: {e}")
            import traceback
            traceback.print_exc()
        
    def clear_plots(self):
        """Clear all visualization data"""
        try:
            self.traffic_data = {direction: [] for direction in self.traffic_data}
            self.reward_history = []
            self.steps = []
            self.ax1.clear()
            self.ax2.clear()
            self.canvas.draw_idle()
            
            # Add a message indicating episode end
            self.ax1.text(0.5, 0.5, 'Episode Ended', 
                         horizontalalignment='center',
                         verticalalignment='center',
                         transform=self.ax1.transAxes)
            self.canvas.draw_idle()
        except Exception as e:
            print(f"Error clearing plots: {e}")
            import traceback
            traceback.print_exc() 