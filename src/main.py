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
    """Main entry point for the traffic simulation"""
    pygame.init()
    simulation = Simulation()
    
    # Set test mode flag
    simulation.test_mode = True
    
    # Run test mode
    simulation.run_test_mode()
    
    pygame.quit()

if __name__ == "__main__":
    main() 