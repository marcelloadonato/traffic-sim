#!/usr/bin/env python3
import sys
import os
import traceback
import pygame
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from src.simulation import Simulation
from src.data_recorder import DataRecorder
from src.config import WIDTH, HEIGHT
from src.shared import PygameContext
from src.ui.main_window import MainWindow

class TestModeThread(QThread):
    """Thread for running the test mode simulation"""
    update_signal = pyqtSignal(object)  # Signal to send updates to main thread
    
    def __init__(self, simulation):
        super().__init__()
        self.simulation = simulation
        self.running = True
        self.msleep(100)  # Initial delay to let UI initialize
    
    def run(self):
        """Run the test mode simulation"""
        # Set initial light states to green for east-west
        self.simulation.ns_light = "red"
        self.simulation.ew_light = "green"
        self.simulation.light_timer = 50  # Start with 50 ticks for green
        self.simulation.test_mode = True  # Mark as test mode
        
        # Create test vehicles with staggered start times
        print("\n=== Starting Test ===")
        print("Creating vehicles with staggered start times...")
        
        # Create vehicles but don't add them to active_vehicles yet
        east_vehicle, west_vehicle, north_vehicle, south_vehicle = self.simulation.create_test_vehicles()
        
        # Store vehicles and their start times
        vehicles_to_add = [
            (east_vehicle, "East", 0),    # East vehicle starts immediately
            (west_vehicle, "West", 20),   # West vehicle starts after 20 ticks
            (north_vehicle, "North", 40),  # North vehicle starts after 40 ticks
            (south_vehicle, "South", 60)   # South vehicle starts after 60 ticks
        ]
        
        # Track vehicle states
        last_logged_tick = -10
        vehicles_added = set()
        
        print("Initial States:")
        for vehicle, direction, start_time in vehicles_to_add:
            print(f"{direction} Vehicle: starts at tick {start_time}")
        print("===================\n")
        
        while self.running:
            try:
                # Add vehicles at their scheduled start times
                for vehicle, direction, start_time in vehicles_to_add:
                    if (vehicle not in vehicles_added and 
                        self.simulation.current_tick >= start_time):
                        self.simulation.active_vehicles.append(vehicle)
                        vehicles_added.add(vehicle)
                        print(f"\n=== Tick {self.simulation.current_tick} ===")
                        print(f"Added {direction} Vehicle to simulation")
                
                # Update light timer and states
                self.simulation.light_timer -= 1
                if self.simulation.light_timer <= 0:
                    # Switch lights
                    if self.simulation.ns_light == "red" and self.simulation.ew_light == "green":
                        self.simulation.ew_light = "yellow"
                        self.simulation.light_timer = 3  # Yellow for 3 ticks
                    elif self.simulation.ns_light == "red" and self.simulation.ew_light == "yellow":
                        self.simulation.ns_light = "green"
                        self.simulation.ew_light = "red"
                        self.simulation.light_timer = 50  # Green for 50 ticks
                    elif self.simulation.ns_light == "green" and self.simulation.ew_light == "red":
                        self.simulation.ns_light = "yellow"
                        self.simulation.light_timer = 3  # Yellow for 3 ticks
                    elif self.simulation.ns_light == "yellow" and self.simulation.ew_light == "red":
                        self.simulation.ns_light = "red"
                        self.simulation.ew_light = "green"
                        self.simulation.light_timer = 50  # Green for 50 ticks
                
                # Store pre-update positions for movement tracking
                pre_east_pos = east_vehicle.interpolated_position if east_vehicle in self.simulation.active_vehicles else None
                pre_west_pos = west_vehicle.interpolated_position if west_vehicle in self.simulation.active_vehicles else None
                pre_north_pos = north_vehicle.interpolated_position if north_vehicle in self.simulation.active_vehicles else None
                pre_south_pos = south_vehicle.interpolated_position if south_vehicle in self.simulation.active_vehicles else None
                
                # Update vehicles
                self.simulation.update_vehicles()
                
                # Calculate movement deltas
                if east_vehicle in self.simulation.active_vehicles and pre_east_pos:
                    east_delta_x = east_vehicle.interpolated_position[0] - pre_east_pos[0]
                    east_delta_y = east_vehicle.interpolated_position[1] - pre_east_pos[1]
                else:
                    east_delta_x = east_delta_y = 0
                
                if west_vehicle in self.simulation.active_vehicles and pre_west_pos:
                    west_delta_x = west_vehicle.interpolated_position[0] - pre_west_pos[0]
                    west_delta_y = west_vehicle.interpolated_position[1] - pre_west_pos[1]
                else:
                    west_delta_x = west_delta_y = 0
                
                if north_vehicle in self.simulation.active_vehicles and pre_north_pos:
                    north_delta_x = north_vehicle.interpolated_position[0] - pre_north_pos[0]
                    north_delta_y = north_vehicle.interpolated_position[1] - pre_north_pos[1]
                else:
                    north_delta_x = north_delta_y = 0
                
                if south_vehicle in self.simulation.active_vehicles and pre_south_pos:
                    south_delta_x = south_vehicle.interpolated_position[0] - pre_south_pos[0]
                    south_delta_y = south_vehicle.interpolated_position[1] - pre_south_pos[1]
                else:
                    south_delta_x = south_delta_y = 0
                
                # Log status every 10 ticks or on significant changes
                should_log = (
                    self.simulation.current_tick - last_logged_tick >= 10 or
                    abs(east_delta_x) > 10 or abs(east_delta_y) > 10 or
                    abs(west_delta_x) > 10 or abs(west_delta_y) > 10 or
                    abs(north_delta_x) > 10 or abs(north_delta_y) > 10 or
                    abs(south_delta_x) > 10 or abs(south_delta_y) > 10 or
                    (east_vehicle in self.simulation.active_vehicles and east_vehicle.state == "waiting") or
                    (west_vehicle in self.simulation.active_vehicles and west_vehicle.state == "waiting") or
                    (north_vehicle in self.simulation.active_vehicles and north_vehicle.state == "waiting") or
                    (south_vehicle in self.simulation.active_vehicles and south_vehicle.state == "waiting")
                )
                
                if should_log:
                    status = {
                        'tick': self.simulation.current_tick,
                        'light_states': {'ns': self.simulation.ns_light, 'ew': self.simulation.ew_light},
                        'light_timer': self.simulation.light_timer,
                        'vehicles': {}
                    }
                    
                    for vehicle, name in [(east_vehicle, 'east'), (west_vehicle, 'west'),
                                        (north_vehicle, 'north'), (south_vehicle, 'south')]:
                        if vehicle in self.simulation.active_vehicles:
                            status['vehicles'][name] = {
                                'position': vehicle.position,
                                'state': vehicle.state,
                                'coordinates': vehicle.interpolated_position,
                                'progress': (vehicle.position_time / vehicle.position_threshold * 100)
                            }
                    
                    self.update_signal.emit(status)
                    last_logged_tick = self.simulation.current_tick
                
                # Increment tick counter
                self.simulation.current_tick += 1
                
                # Check if all vehicles have completed their routes
                if not self.simulation.active_vehicles and len(vehicles_added) == len(vehicles_to_add):
                    print("\n=== Test Complete ===")
                    print("All vehicles have completed their routes")
                    self.running = False
                    break
                
                # Add a small delay to prevent overwhelming the main thread
                self.msleep(50)  # 50ms delay between updates
                
            except Exception as e:
                print(f"Error in test mode thread: {e}")
                self.running = False
                break
    
    def stop(self):
        """Stop the test mode thread"""
        self.running = False

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
        try:
            pygame.init()
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("Traffic Simulation")
            pygame_clock = pygame.time.Clock()
        except pygame.error as e:
            print(f"Error initializing Pygame: {e}")
            return 1
        
        # Initialize Pygame context
        try:
            PygameContext.initialize(screen)
        except Exception as e:
            print(f"Error initializing PygameContext: {e}")
            pygame.quit()
            return 1
        
        # Create simulation and data recorder
        try:
            simulation = Simulation()
            data_recorder = DataRecorder()
            
            # Connect data recorder to simulation
            simulation.set_data_recorder(data_recorder)
        except Exception as e:
            print(f"Error creating simulation: {e}")
            pygame.quit()
            return 1
        
        # Create the dashboard window
        try:
            dashboard = MainWindow(simulation)
            dashboard.show()
            dashboard.raise_()
        except Exception as e:
            print(f"Error creating dashboard: {e}")
            pygame.quit()
            return 1
        
        # Create a timer for updating both simulations
        update_timer = QTimer()
        
        def update_simulation():
            try:
                # Process PyQt events
                app.processEvents()
                
                # Update simulation
                if test_mode:
                    # Draw everything
                    simulation.draw(None)
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
            except pygame.error as e:
                if "display Surface quit" in str(e):
                    # Handle graceful shutdown
                    update_timer.stop()
                    pygame.quit()
                    app.quit()
                    return
                else:
                    # Re-raise other pygame errors
                    raise
            except Exception as e:
                print(f"Error in update_simulation: {e}")
                update_timer.stop()
                pygame.quit()
                app.quit()
                return
        
        # Connect timer to update function
        update_timer.timeout.connect(update_simulation)
        update_timer.start(16)  # ~60 FPS
        
        if test_mode:
            # Create and start test mode thread
            test_thread = TestModeThread(simulation)
            
            def handle_test_update(status):
                """Handle updates from test mode thread"""
                print(f"\n=== Tick {status['tick']} ===")
                print(f"Light States: NS={status['light_states']['ns']}, EW={status['light_states']['ew']}, Timer={status['light_timer']}")
                
                for name, vehicle_data in status['vehicles'].items():
                    print(f"\n{name.capitalize()} Vehicle:")
                    print(f"Position: {vehicle_data['position']}")
                    print(f"State: {vehicle_data['state']}")
                    print(f"Coordinates: {vehicle_data['coordinates']}")
                    print(f"Progress: {vehicle_data['progress']:.2f}%")
                
                print("========================================")
            
            test_thread.update_signal.connect(handle_test_update)
            test_thread.start()
        
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