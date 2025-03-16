import sys
import pygame
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from src.config import WIDTH, HEIGHT, WHITE, DEBUG_MODE, SLOW_MODE
from src.simulation import Simulation
from src.data_recorder import DataRecorder
from src.shared import PygameContext
from src.ui.main_window import MainWindow

def main():
    # Initialize PyQt application
    app = QApplication(sys.argv)
    
    # Initialize pygame context
    pygame_context = PygameContext.init(WIDTH, HEIGHT)
    
    # Create simulation and data recorder
    simulation = Simulation()
    data_recorder = DataRecorder()
    
    # Connect data recorder to simulation
    simulation.set_data_recorder(data_recorder)
    
    # Create and show the control window
    control_window = MainWindow(simulation)
    control_window.show()
    
    # Connect the RL agent's signals to the visualization panel
    control_window.rl_agent.traffic_update.connect(
        control_window.visualization_panel.update_traffic_plot
    )
    control_window.rl_agent.reward_update.connect(
        control_window.visualization_panel.update_reward_plot
    )
    
    # Create a timer for updating the simulation
    def update_simulation():
        if simulation.running:
            try:
                # Step the simulation
                simulation.step(data_recorder)
                
                # Update the game window
                pygame.display.flip()
                
                # Control frame rate
                pygame.time.Clock().tick(60)
            except Exception as e:
                print(f"Error in simulation step: {str(e)}")
                simulation.running = False
        else:
            # Stop the timer when simulation ends
            timer.stop()
            app.quit()
    
    # Create and start the timer
    timer = QTimer()
    timer.timeout.connect(update_simulation)
    timer.start(16)  # Update every 16ms (approximately 60 FPS)
    
    # Start the PyQt event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 