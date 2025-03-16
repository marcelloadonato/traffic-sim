#!/usr/bin/env python3
import sys
import os
import traceback
import pygame
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
from src.simulation import Simulation
from src.data_recorder import DataRecorder
from src.config import WIDTH, HEIGHT
from src.shared import PygameContext
from src.ui.main_window import MainWindow

def main():
    try:
        # Add the project root directory to Python path for imports
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.append(project_root)
        
        # Check for test mode argument
        test_mode = "--test" in sys.argv
        
        # Initialize PyQt application
        app = QApplication(sys.argv)
        
        # Initialize Pygame
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Traffic Simulation")
        pygame_clock = pygame.time.Clock()
        
        # Initialize Pygame context
        PygameContext.initialize(screen)
        
        # Create simulation and data recorder
        simulation = Simulation()
        data_recorder = DataRecorder()
        
        # Connect data recorder to simulation
        simulation.set_data_recorder(data_recorder)
        
        # Create the dashboard window
        dashboard = MainWindow(simulation)
        
        # Show the dashboard window (explicitly set it as visible and raise it)
        dashboard.show()
        dashboard.raise_()
        
        if test_mode:
            # Test mode setup
            simulation.create_test_vehicle()
        
        # Create a timer for updating both simulations
        update_timer = QTimer()
        
        def update_simulation():
            # Process PyQt events
            app.processEvents()
            
            # Process Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    update_timer.stop()
                    pygame.quit()
                    app.quit()
                    return
            
            # Update simulation
            if test_mode:
                # Run one step of test mode
                if simulation.running:
                    # Update traffic lights
                    simulation.update_traffic_lights()
                    
                    # Update vehicles
                    simulation.update_vehicles()
                    
                    # Draw everything
                    simulation.draw(None)
                    
                    # Increment tick
                    simulation.current_tick += 1
                else:
                    update_timer.stop()
                    pygame.quit()
                    app.quit()
                    return
            else:
                # Normal simulation mode
                if simulation.running:
                    simulation.step(data_recorder)
                else:
                    update_timer.stop()
                    pygame.quit()
                    app.quit()
                    return
            
            # Update metrics in the dashboard
            metrics = simulation.get_metrics()
            dashboard.metrics_panel.update_metrics(metrics)
            
            # Update traffic counts
            traffic_counts = simulation.get_traffic_counts()
            dashboard.visualization_panel.update_traffic_plot(traffic_counts)
            
            # Control frame rate
            pygame_clock.tick(30)
        
        # Connect timer to update function
        update_timer.timeout.connect(update_simulation)
        update_timer.start(16)  # ~60 FPS
        
        # Enter the Qt event loop
        return app.exec_()
        
    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        print("\nDetailed error traceback:")
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"Error running the simulation: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 