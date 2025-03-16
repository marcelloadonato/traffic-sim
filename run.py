#!/usr/bin/env python3
import sys
import os
import traceback
import pygame
from src.simulation import Simulation
from src.data_recorder import DataRecorder
from src.config import WIDTH, HEIGHT
from src.shared import PygameContext

def main():
    try:
        # Add the project root directory to Python path for imports
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.append(project_root)
        
        # Initialize Pygame
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Traffic Simulation")
        
        # Initialize Pygame context
        PygameContext.initialize(screen)
        
        # Check for test mode argument
        test_mode = "--test" in sys.argv
        
        # Create simulation instance
        simulation = Simulation()
        
        if test_mode:
            # Run in test mode with a single vehicle
            simulation.run_test_mode()
        else:
            # Normal simulation mode
            data_recorder = DataRecorder()
            simulation.set_data_recorder(data_recorder)
            
            # Main game loop
            while simulation.running:
                simulation.step(data_recorder)
        
        pygame.quit()
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
    return 0

if __name__ == "__main__":
    sys.exit(main()) 