import sys
import pygame
from config import WIDTH, HEIGHT, WHITE, DEBUG_MODE, SLOW_MODE
from simulation import Simulation
from data_recorder import DataRecorder
from shared import PygameContext

def main():
    # Initialize pygame context
    pygame_context = PygameContext.init(WIDTH, HEIGHT)
    
    # Create simulation and data recorder
    simulation = Simulation()
    data_recorder = DataRecorder()
    
    # Main game loop
    while simulation.running:
        simulation.step(data_recorder)
    
    # Clean up
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main() 