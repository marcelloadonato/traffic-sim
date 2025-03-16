import random
import pygame
import numpy as np
import torch
from src.config import WIDTH, HEIGHT, BUILDING_COLORS, DEBUG_MODE, SLOW_MODE, EPISODE_LENGTH, WHITE, BLACK, LANES, SPEED_SLIDER, TRAINING_SLIDER, MAX_VEHICLES_PER_LANE
from src.visualization import draw_buildings, draw_road, draw_traffic_lights, draw_vehicle, draw_debug_info
from src.vehicle_spawner import generate_vehicle_spawn_schedule, spawn_vehicles
from src.collision import check_collision, get_vehicle_position
from src.shared import get_screen, get_clock
from src.rl_agent import TrafficRLAgent

# Check if CUDA is available
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

"""
Traffic Simulation with Reinforcement Learning

Key Components:
- set_traffic_lights: RL agent decides light states here
- update_vehicles: Handles vehicle movement and state changes
- handle_events: Processes user input and simulation controls
- tutorial_mode: Educational mode with step-by-step explanations
"""

class Simulation:
    def __init__(self):
        # Initialize buildings
        self.buildings = []
        # Tutorial mode settings
        self.tutorial_mode = False
        self.tutorial_step = 0
        self.tutorial_messages = [
            "Vehicles spawn and move toward the intersection.",
            "RL agent observes waiting vehicles and picks a light state.",
            "Reward reflects commute time and satisfaction—watch it evolve!"
        ]
        # Manual control mode
        self.manual_mode = False
        # Traffic generation mode
        self.traffic_mode = "Random"  # Default mode
        # Current simulation mode
        self.simulation_mode = "RL"  # Default mode
        
        # Generate buildings in each quadrant
        self._generate_buildings()
        
        # Initialize traffic counts
        self.traffic_counts = {
            'north': 0,
            'south': 0,
            'east': 0,
            'west': 0
        }
        
        # Initialize simulation state
        self.reset()
        self.episode_ended = False
        self.current_fps = SPEED_SLIDER['default_fps']
        self.current_training_steps = TRAINING_SLIDER['default_steps']
        self.slider_dragging = False
        self.training_slider_dragging = False
        
        # Initialize RL agent
        self.rl_agent = TrafficRLAgent(self)
        self.training_in_progress = False
        
        # Initialize tensors for GPU acceleration
        self.vehicle_positions = torch.zeros((MAX_VEHICLES_PER_LANE * 4, 2), device=DEVICE)  # For all possible vehicles
        self.vehicle_states = torch.zeros((MAX_VEHICLES_PER_LANE * 4, 4), device=DEVICE)  # [waiting, moving, arrived, satisfaction]
        self.light_states = torch.zeros(2, device=DEVICE)  # [ns_light, ew_light]
    
    def _generate_buildings(self):
        """Helper method to generate buildings in all four quadrants"""
        # Define quadrant boundaries
        quadrants = [
            # (x_min, x_max, y_min, y_max)
            (50, WIDTH//2 - 100//2 - 80, 50, HEIGHT//2 - 100//2 - 80),  # Northwest
            (WIDTH//2 + 100//2 + 30, WIDTH - 100, 50, HEIGHT//2 - 100//2 - 80),  # Northeast
            (50, WIDTH//2 - 100//2 - 80, HEIGHT//2 + 100//2 + 30, HEIGHT - 100),  # Southwest
            (WIDTH//2 + 100//2 + 30, WIDTH - 100, HEIGHT//2 + 100//2 + 30, HEIGHT - 100)  # Southeast
        ]
        
        # Generate buildings for each quadrant
        for x_min, x_max, y_min, y_max in quadrants:
            for _ in range(5):
                x = random.randint(x_min, x_max)
                y = random.randint(y_min, y_max)
                width = random.randint(40, 100)
                height = random.randint(40, 100)
                color = random.choice(BUILDING_COLORS)
                self.buildings.append((x, y, width, height, color))
    
    def reset(self):
        """Reset the simulation to its initial state"""
        self.active_vehicles = []
        self.removed_vehicles = []
        self.spawn_schedule = generate_vehicle_spawn_schedule()
        self.ns_light = "green"  # North-South light starts green
        self.ew_light = "red"    # East-West light starts red
        self.ns_yellow_countdown = 0
        self.ew_yellow_countdown = 0
        self.current_tick = 0
        self.running = True
        self.episode_ended = False
        self.light_change_count = 0  # Track number of light changes per episode
    
    def set_data_recorder(self, data_recorder):
        """Set the data recorder for the simulation"""
        self.data_recorder = data_recorder
        data_recorder.set_simulation(self)  # Set the simulation reference
    
    def get_avg_commute_time(self):
        """Get average commute time of completed vehicles"""
        if not self.removed_vehicles:
            return 0
        return sum(v.commute_time for v in self.removed_vehicles) / len(self.removed_vehicles)
    
    def get_avg_satisfaction(self):
        """Get average satisfaction of all vehicles"""
        all_vehicles = self.active_vehicles + self.removed_vehicles
        if not all_vehicles:
            return 0
        return sum(v.satisfaction for v in all_vehicles) / len(all_vehicles)
    
    def get_waiting_vehicles(self):
        """Get number of waiting vehicles per direction"""
        waiting = {'north': 0, 'south': 0, 'east': 0, 'west': 0}
        for vehicle in self.active_vehicles:
            if vehicle.state == "waiting" and vehicle.position in waiting:
                waiting[vehicle.position] += 1
        return waiting
    
    def update_traffic_lights(self):
        """Update traffic light states with yellow transitions"""
        # Update NS light
        if self.ns_light == "yellow":
            self.ns_yellow_countdown -= 1
            if self.ns_yellow_countdown <= 0:
                self.ns_light = "red"
                self.ns_yellow_countdown = 0
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.record_light_change()
        
        # Update EW light
        if self.ew_light == "yellow":
            self.ew_yellow_countdown -= 1
            if self.ew_yellow_countdown <= 0:
                self.ew_light = "red"
                self.ew_yellow_countdown = 0
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.record_light_change()
    
    def set_traffic_lights(self, action):
        """Set traffic lights based on action with yellow transitions"""
        # Only change lights if they're not in yellow transition
        if self.ns_light == "yellow" or self.ew_light == "yellow":
            return
            
        if action == 0:  # NS green
            if self.ns_light != "green":
                # Start yellow transition for current green light
                if self.ew_light == "green":
                    self.ew_light = "yellow"
                    self.ew_yellow_countdown = 3  # 3 ticks of yellow
                # Set NS to green after yellow transition
                self.ns_light = "green"
                self.ns_yellow_countdown = 0
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.record_light_change()
        
        elif action == 1:  # EW green
            if self.ew_light != "green":
                # Start yellow transition for current green light
                if self.ns_light == "green":
                    self.ns_light = "yellow"
                    self.ns_yellow_countdown = 3  # 3 ticks of yellow
                # Set EW to green after yellow transition
                self.ew_light = "green"
                self.ew_yellow_countdown = 0
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.record_light_change()
    
    def handle_events(self):
        """Handle user input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_d:
                    global DEBUG_MODE
                    DEBUG_MODE = not DEBUG_MODE
                elif event.key == pygame.K_s:
                    global SLOW_MODE
                    SLOW_MODE = not SLOW_MODE
                elif event.key == pygame.K_e:
                    if not self.episode_ended:
                        self.episode_ended = True
                        if hasattr(self, 'data_recorder'):
                            self.data_recorder.end_episode(self.light_change_count)
                elif event.key == pygame.K_n:
                    if self.episode_ended:
                        self.reset()
                elif event.key == pygame.K_c and self.tutorial_mode:
                    self.tutorial_step += 1
                elif self.manual_mode:
                    if event.key == pygame.K_SPACE:
                        # Only change lights if they're not in yellow transition
                        if self.ns_light != "yellow" and self.ew_light != "yellow":
                            # Start yellow transition for current green light
                            if self.ns_light == "green":
                                self.ns_light = "yellow"
                                self.ns_yellow_countdown = 3
                            elif self.ew_light == "green":
                                self.ew_light = "yellow"
                                self.ew_yellow_countdown = 3
                            # Set the other light to green
                            if self.ns_light == "yellow":
                                self.ew_light = "green"
                            else:
                                self.ns_light = "green"
                            if hasattr(self, 'data_recorder'):
                                self.data_recorder.record_light_change()
    
    def update_vehicles(self):
        """Update all active vehicles with GPU acceleration"""
        # Update vehicle positions tensor
        for i, vehicle in enumerate(self.active_vehicles):
            if i >= MAX_VEHICLES_PER_LANE * 4:
                break
            pos = get_vehicle_position(vehicle)
            self.vehicle_positions[i] = torch.tensor(pos, device=DEVICE)
        
        # Update vehicles in parallel where possible
        for vehicle in self.active_vehicles[:]:
            # Set the collision detection function with GPU acceleration
            vehicle.check_collision_ahead = lambda: check_collision(vehicle, 
                                                                  vehicle.route[vehicle.route.index(vehicle.position) + 1] 
                                                                  if vehicle.route.index(vehicle.position) < len(vehicle.route) - 1 
                                                                  else None,
                                                                  self.active_vehicles)
            
            # Determine which light applies to this vehicle
            if vehicle.start_position in ['north', 'south']:
                applicable_light = self.ns_light
            else:  # east or west
                applicable_light = self.ew_light
            
            # Update light states tensor
            self.light_states = torch.tensor([
                1.0 if self.ns_light == "green" else 0.0,
                1.0 if self.ew_light == "green" else 0.0
            ], device=DEVICE)
            
            # Update the vehicle with the applicable light
            vehicle.update(applicable_light)
            
            # Check if vehicle has arrived at destination
            if vehicle.state == "arrived" or vehicle.position == vehicle.destination:
                # Record completion data before removing
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.record_vehicle_completion(vehicle)
                
                # Remove from active and add to removed
                self.removed_vehicles.append(vehicle)
                self.active_vehicles.remove(vehicle)
                
                if DEBUG_MODE:
                    print(f"Vehicle completed journey: {vehicle.start_position} -> {vehicle.destination} in {vehicle.commute_time} ticks")
        
        # Update traffic counts based on mode
        if self.traffic_mode == "Pattern":
            # Implement pattern-based traffic generation
            pass
        elif self.traffic_mode == "Peak Hours":
            # Implement peak hours traffic generation
            pass
        else:  # Random mode
            # Use existing random generation
            pass
    
    def draw(self, data_recorder):
        """Draw the current simulation state"""
        screen = get_screen()
        screen.fill(WHITE)
        
        # Draw buildings
        draw_buildings(self.buildings)
        
        # Draw road and traffic lights
        draw_road()
        draw_traffic_lights(self.ns_light, self.ew_light)
        
        # Draw vehicles
        for vehicle in self.active_vehicles:
            draw_vehicle(vehicle, DEBUG_MODE)
        
        # Draw debug info if debug mode is enabled
        if DEBUG_MODE:
            # Calculate lane occupancy
            lane_counts = {}
            for vehicle in self.active_vehicles:
                if vehicle.position in ['north', 'south', 'east', 'west']:
                    lane_counts[vehicle.position] = lane_counts.get(vehicle.position, 0) + 1
            
            draw_debug_info(self.ns_light, self.ew_light, self.active_vehicles, 
                          self.spawn_schedule, self.current_tick, EPISODE_LENGTH, lane_counts)
        
        # Force display update
        pygame.display.flip()
    
    def update_simulation(self):
        """Update the simulation for one step without drawing (used by RL)"""
        if not self.episode_ended:
            # Update simulation state
            self.update_traffic_lights()
            
            # Spawn new vehicles if needed
            spawn_vehicles(self.current_tick, self.spawn_schedule, self.active_vehicles)
            
            # Update vehicles
            self.update_vehicles()
            
            # Record data if data recorder exists
            if hasattr(self, 'data_recorder'):
                waiting_count = sum(1 for v in self.active_vehicles if v.state == "waiting")
                moving_count = sum(1 for v in self.active_vehicles if v.state == "moving")
                arrived_count = len(self.removed_vehicles)
                avg_satisfaction = self.get_avg_satisfaction()
                
                self.data_recorder.record_tick(
                    self.current_tick,
                    f"NS:{self.ns_light},EW:{self.ew_light}",
                    waiting_count,
                    moving_count,
                    arrived_count,
                    avg_satisfaction
                )
            
            # Increment tick counter
            self.current_tick += 1
            
            # Check if episode should end
            if self.current_tick >= EPISODE_LENGTH or (not self.active_vehicles and not self.spawn_schedule):
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.end_episode(self.light_change_count)
                self.episode_ended = True
                print("Episode ended automatically")
    
    def get_observation(self):
        """Get the current observation state for the RL agent using GPU acceleration"""
        # Update vehicle states tensor
        for i, vehicle in enumerate(self.active_vehicles):
            if i >= MAX_VEHICLES_PER_LANE * 4:
                break
            self.vehicle_states[i] = torch.tensor([
                1.0 if vehicle.state == "waiting" else 0.0,
                1.0 if vehicle.state == "moving" else 0.0,
                1.0 if vehicle.state == "arrived" else 0.0,
                vehicle.satisfaction
            ], device=DEVICE)
        
        # Calculate waiting vehicles per direction using GPU
        waiting = torch.zeros(4, device=DEVICE)  # [north, south, east, west]
        for i, vehicle in enumerate(self.active_vehicles):
            if i >= MAX_VEHICLES_PER_LANE * 4:
                break
            if vehicle.state == "waiting":
                if vehicle.position == "north":
                    waiting[0] += 1
                elif vehicle.position == "south":
                    waiting[1] += 1
                elif vehicle.position == "east":
                    waiting[2] += 1
                elif vehicle.position == "west":
                    waiting[3] += 1
        
        # Convert to numpy for RL agent
        observation = waiting.cpu().numpy().astype(np.int32)
        return observation
    
    def step(self, data_recorder):
        """Update the simulation state with GPU acceleration"""
        # Handle events
        self.handle_events()
        
        # Update traffic lights based on mode
        if self.simulation_mode == "RL":
            try:
                # Get observation and action from RL agent
                observation = self.get_observation()
                action = self.rl_agent.predict(observation)
                self.set_traffic_lights(action)
            except Exception as e:
                print(f"Error in RL mode: {str(e)}")
                # Fallback to alternating pattern if RL fails
                if self.current_tick % 100 < 50:
                    self.set_traffic_lights(0)  # NS green
                else:
                    self.set_traffic_lights(1)  # EW green
        elif self.manual_mode:
            # Manual control is handled in handle_events
            pass
        else:  # Tutorial mode
            # Tutorial mode uses simple alternating pattern
            if self.current_tick % 100 < 50:
                self.set_traffic_lights(0)  # NS green
            else:
                self.set_traffic_lights(1)  # EW green
        
        # Update traffic light states
        self.update_traffic_lights()
        
        # Spawn new vehicles if needed
        spawn_vehicles(self.current_tick, self.spawn_schedule, self.active_vehicles)
        
        # Update vehicles with GPU acceleration
        self.update_vehicles()
        
        # Update current tick
        self.current_tick += 1
        
        # Record data for visualization
        waiting_count = sum(1 for v in self.active_vehicles if v.state == "waiting")
        moving_count = sum(1 for v in self.active_vehicles if v.state == "moving")
        arrived_count = len(self.removed_vehicles)
        avg_satisfaction = self.get_avg_satisfaction()
        
        if hasattr(self, 'data_recorder'):
            data_recorder.record_tick(self.current_tick, f"NS:{self.ns_light},EW:{self.ew_light}", 
                                    waiting_count, moving_count, arrived_count, avg_satisfaction)
        
        # Draw everything
        self.draw(data_recorder)
        
        # Control simulation speed using the fps value
        clock = get_clock()
        if SLOW_MODE:
            clock.tick(10)  # Slower for debugging
        else:
            clock.tick(self.current_fps)
    
    def set_traffic_mode(self, mode):
        """Set the traffic generation mode"""
        self.traffic_mode = mode
        # Reset traffic counts when mode changes
        self.traffic_counts = {direction: 0 for direction in self.traffic_counts}
        
    def get_traffic_counts(self):
        """Get current traffic counts by direction"""
        # Initialize counts
        counts = {
            'north': 0,
            'south': 0,
            'east': 0,
            'west': 0
        }
        
        # Count vehicles in each direction
        for vehicle in self.active_vehicles:
            if vehicle.position in counts:
                counts[vehicle.position] += 1
        
        # Update traffic counts
        self.traffic_counts = counts
        return self.traffic_counts
    
    def set_mode(self, mode):
        """Set the simulation mode (RL, Manual, or Tutorial)"""
        self.simulation_mode = mode
        self.tutorial_mode = (mode == "Tutorial")
        self.manual_mode = (mode == "Manual")
        
        # Reset tutorial step when entering tutorial mode
        if self.tutorial_mode:
            self.tutorial_step = 0
            
    def draw_tutorial_message(self):
        """Draw the current tutorial message"""
        if self.tutorial_step < len(self.tutorial_messages):
            message = self.tutorial_messages[self.tutorial_step]
            font = pygame.font.Font(None, 36)
            text = font.render(message, True, WHITE)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT - 50))
            get_screen().blit(text, text_rect)
            
            # Draw instruction
            instruction = "Press SPACE to continue"
            instruction_font = pygame.font.Font(None, 24)
            instruction_text = instruction_font.render(instruction, True, WHITE)
            instruction_rect = instruction_text.get_rect(center=(WIDTH//2, HEIGHT - 20))
            get_screen().blit(instruction_text, instruction_rect) 