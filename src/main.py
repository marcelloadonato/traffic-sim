import sys
import pygame
import threading
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from src.config import WIDTH, HEIGHT, WHITE, DEBUG_MODE, SLOW_MODE
from src.simulation import Simulation
from src.data_recorder import DataRecorder
from src.shared import PygameContext
from src.ui.main_window import MainWindow

class SimulationThread(QThread):
    """Thread for running the Pygame simulation"""
    metrics_updated = pyqtSignal(dict)
    traffic_updated = pyqtSignal(dict)
    
    def __init__(self, simulation, data_recorder):
        super().__init__()
        self.simulation = simulation
        self.data_recorder = data_recorder
        self.running = True
        
    def run(self):
        # Initialize pygame in this thread
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Traffic Simulation")
        clock = pygame.time.Clock()
        
        while self.running:
            # Handle events in this thread
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            # Step the simulation
            self.simulation.step(self.data_recorder)
            
            # Get metrics for PyQt window
            metrics = self.simulation.get_metrics()
            self.metrics_updated.emit(metrics)
            
            # Get traffic counts for PyQt window
            traffic_counts = self.simulation.get_traffic_counts()
            self.traffic_updated.emit(traffic_counts)
            
            # Update the game window
            pygame.display.flip()
            
            # Control frame rate
            clock.tick(60)
        
        # Cleanup when thread finishes
        pygame.quit()
    
    def stop(self):
        self.running = False
        self.wait()

def main():
    # Initialize PyQt application first
    app = QApplication(sys.argv)
    
    # Create simulation and data recorder
    simulation = Simulation()
    data_recorder = DataRecorder()
    
    # Connect data recorder to simulation
    simulation.set_data_recorder(data_recorder)
    
    # Create the control window
    main_window = MainWindow(simulation)
    
    # Create and start the simulation thread
    sim_thread = SimulationThread(simulation, data_recorder)
    
    # Connect signals from simulation thread to main window
    sim_thread.metrics_updated.connect(main_window.metrics_panel.update_metrics)
    sim_thread.traffic_updated.connect(main_window.visualization_panel.update_traffic_plot)
    
    # Show the main window
    main_window.show()
    main_window.raise_()
    
    # Start the simulation thread
    sim_thread.start()
    
    # Run the PyQt event loop
    exit_code = app.exec_()
    
    # Clean up when application exits
    sim_thread.stop()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 