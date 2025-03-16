import random
import pygame
import numpy as np
import torch
from config import WIDTH, HEIGHT, BUILDING_COLORS, DEBUG_MODE, SLOW_MODE, EPISODE_LENGTH, WHITE, BLACK, LANES, SPEED_SLIDER, TRAINING_SLIDER, MAX_VEHICLES_PER_LANE
from visualization import draw_buildings, draw_road, draw_traffic_lights, draw_vehicle, draw_stats, draw_debug_info, draw_speed_slider, draw_training_slider
from vehicle_spawner import generate_vehicle_spawn_schedule, spawn_vehicles
from collision import check_collision, get_vehicle_position
from shared import get_screen, get_clock
from rl_agent import TrafficRLAgent

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
        
        # Northwest quadrant
        for _ in range(5):
            x = random.randint(50, WIDTH//2 - 100//2 - 80)
            y = random.randint(50, HEIGHT//2 - 100//2 - 80)
            width = random.randint(40, 100)
            height = random.randint(40, 100)
            color = random.choice(BUILDING_COLORS)
            self.buildings.append((x, y, width, height, color))

        # Northeast quadrant
        for _ in range(5):
            x = random.randint(WIDTH//2 + 100//2 + 30, WIDTH - 100)
            y = random.randint(50, HEIGHT//2 - 100//2 - 80)
            width = random.randint(40, 100)
            height = random.randint(40, 100)
            color = random.choice(BUILDING_COLORS)
            self.buildings.append((x, y, width, height, color))

        # Southwest quadrant
        for _ in range(5):
            x = random.randint(50, WIDTH//2 - 100//2 - 80)
            y = random.randint(HEIGHT//2 + 100//2 + 30, HEIGHT - 100)
            width = random.randint(40, 100)
            height = random.randint(40, 100)
            color = random.choice(BUILDING_COLORS)
            self.buildings.append((x, y, width, height, color))

        # Southeast quadrant
        for _ in range(5):
            x = random.randint(WIDTH//2 + 100//2 + 30, WIDTH - 100)
            y = random.randint(HEIGHT//2 + 100//2 + 30, HEIGHT - 100)
            width = random.randint(40, 100)
            height = random.randint(40, 100)
            color = random.choice(BUILDING_COLORS)
            self.buildings.append((x, y, width, height, color))
        
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
    
    def set_traffic_lights(self, action):
        """Set traffic lights based on RL agent action"""
        if action == 0:  # NS green
            if self.ew_light == "green":
                self.ew_light = "yellow"
                self.ew_yellow_countdown = 30
                self.light_change_count += 1
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.record_light_change()
        else:  # EW green
            if self.ns_light == "green":
                self.ns_light = "yellow"
                self.ns_yellow_countdown = 30
                self.light_change_count += 1
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.record_light_change()
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check if clicked on speed slider handle
                    if hasattr(self, 'slider_handle_rect') and self.slider_handle_rect.collidepoint(event.pos):
                        self.slider_dragging = True
                    elif hasattr(self, 'training_slider_handle_rect') and self.training_slider_handle_rect.collidepoint(event.pos):
                        self.training_slider_dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click
                    self.slider_dragging = False
                    self.training_slider_dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.slider_dragging and hasattr(self, 'slider_handle_rect'):
                    # Update FPS based on slider position
                    x = max(SPEED_SLIDER['x'], min(event.pos[0], SPEED_SLIDER['x'] + SPEED_SLIDER['width']))
                    rel_x = x - SPEED_SLIDER['x']
                    self.current_fps = int(SPEED_SLIDER['min_fps'] + (rel_x / SPEED_SLIDER['width']) * 
                                         (SPEED_SLIDER['max_fps'] - SPEED_SLIDER['min_fps']))
                elif self.training_slider_dragging and hasattr(self, 'training_slider_handle_rect'):
                    # Update training steps based on slider position
                    x = max(TRAINING_SLIDER['x'], min(event.pos[0], TRAINING_SLIDER['x'] + TRAINING_SLIDER['width']))
                    rel_x = x - TRAINING_SLIDER['x']
                    self.current_training_steps = int(TRAINING_SLIDER['min_steps'] + (rel_x / TRAINING_SLIDER['width']) * 
                                                  (TRAINING_SLIDER['max_steps'] - TRAINING_SLIDER['min_steps']))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_d:  # Toggle debug mode
                    global DEBUG_MODE
                    DEBUG_MODE = not DEBUG_MODE
                    print(f"Debug mode: {'ON' if DEBUG_MODE else 'OFF'}")
                elif event.key == pygame.K_s:  # Toggle slow mode
                    global SLOW_MODE
                    SLOW_MODE = not SLOW_MODE
                    print(f"Slow mode: {'ON' if SLOW_MODE else 'OFF'}")
                elif event.key == pygame.K_e:  # End episode
                    if not self.episode_ended:
                        self.episode_ended = True
                        print("Episode ended manually")
                elif event.key == pygame.K_n:  # Start new episode
                    if self.episode_ended:
                        self.reset()
                        print("Starting new episode")
                elif event.key == pygame.K_t:  # Toggle training mode
                    if not self.training_in_progress:
                        self.training_in_progress = True
                        self.rl_agent.total_timesteps = self.current_training_steps
                        self.rl_agent.train()
                        self.training_in_progress = False
                        print(f"Training completed with {self.current_training_steps} steps")
                elif event.key == pygame.K_m:  # Toggle manual mode
                    if not self.training_in_progress:
                        self.manual_mode = not self.manual_mode
                        print(f"Manual mode: {'ON' if self.manual_mode else 'OFF'}")
                elif event.key == pygame.K_SPACE and self.manual_mode:  # Toggle lights manually
                    if self.ns_light == "green":
                        self.ns_light = "yellow"
                        self.ns_yellow_countdown = 30
                    else:
                        self.ew_light = "yellow"
                        self.ew_yellow_countdown = 30
                elif event.key == pygame.K_c and self.tutorial_mode:  # Continue tutorial
                    self.tutorial_step += 1
    
    def update_traffic_lights(self):
        """Update traffic light states"""
        if self.ns_light == "yellow":
            self.ns_yellow_countdown -= 1
            if self.ns_yellow_countdown <= 0:
                self.ns_light = "red"
                self.ew_light = "green"
                self.light_change_count += 1
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.record_light_change()
        
        if self.ew_light == "yellow":
            self.ew_yellow_countdown -= 1
            if self.ew_yellow_countdown <= 0:
                self.ew_light = "red"
                self.ns_light = "green"
                self.light_change_count += 1
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
        
        # Draw tutorial message if in tutorial mode
        if self.tutorial_mode and self.tutorial_step < len(self.tutorial_messages):
            font = pygame.font.SysFont('Arial', 24)
            message = self.tutorial_messages[self.tutorial_step]
            text = font.render(message, True, BLACK)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 50))
            continue_text = font.render("Press C to continue", True, BLACK)
            screen.blit(continue_text, (WIDTH//2 - continue_text.get_width()//2, 80))
        
        # Draw mode indicators
        if self.tutorial_mode:
            mode_text = "Tutorial Mode"
        elif self.manual_mode:
            mode_text = "Manual Mode"
        else:
            mode_text = "RL Mode"
        font = pygame.font.SysFont('Arial', 20)
        text = font.render(mode_text, True, BLACK)
        screen.blit(text, (10, 10))
        
        # Calculate and draw stats
        waiting_count = sum(1 for v in self.active_vehicles if v.state == "waiting")
        moving_count = sum(1 for v in self.active_vehicles if v.state == "moving")
        arrived_count = len(self.removed_vehicles)
        avg_satisfaction = self.get_avg_satisfaction()
        
        draw_stats(waiting_count, moving_count, arrived_count, avg_satisfaction, 
                  self.data_recorder.current_episode if hasattr(self, 'data_recorder') else 0, 
                  self.current_tick)
        
        # Record data
        if hasattr(self, 'data_recorder'):
            data_recorder.record_tick(self.current_tick, f"NS:{self.ns_light},EW:{self.ew_light}", 
                                    waiting_count, moving_count, arrived_count, avg_satisfaction)
        
        # Draw debug info
        if DEBUG_MODE:
            # Calculate lane occupancy
            lane_counts = {}
            for vehicle in self.active_vehicles:
                if vehicle.position in ['north', 'south', 'east', 'west']:
                    lane_counts[vehicle.position] = lane_counts.get(vehicle.position, 0) + 1
            
            draw_debug_info(self.ns_light, self.ew_light, self.active_vehicles, 
                          self.spawn_schedule, self.current_tick, EPISODE_LENGTH, lane_counts)
        
        # Draw episode state message
        if self.episode_ended:
            font = pygame.font.SysFont('Arial', 24)
            text = font.render("Episode Ended - Press N to start new episode", True, BLACK)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(text, text_rect)
        
        # Draw the speed slider and store its handle rect
        self.slider_handle_rect = draw_speed_slider(self.current_fps)
        
        # Draw the training steps slider and store its handle rect
        self.training_slider_handle_rect = draw_training_slider(self.current_training_steps)
        
        # Show training status if in progress
        if self.training_in_progress:
            font = pygame.font.SysFont('Arial', 24)
            text = font.render(f"Training in progress: {self.current_training_steps} steps", True, BLACK)
            text_rect = text.get_rect(center=(WIDTH//2, 50))
            screen.blit(text, text_rect)
        
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
        
        # Update vehicles with GPU acceleration
        self.update_vehicles()
        
        # Spawn new vehicles if needed
        spawn_vehicles(self.current_tick, self.spawn_schedule, self.active_vehicles)
        
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
        
        # Update current tick
        self.current_tick += 1
        
        # Draw everything
        self.draw(data_recorder)
        
        # Update tutorial message if in tutorial mode
        if self.tutorial_mode:
            self.draw_tutorial_message()
        
        # Control simulation speed using the slider
        clock = get_clock()
        if SLOW_MODE:
            clock.tick(10)  # Slower for debugging
        else:
            clock.tick(self.current_fps)  # Use slider-controlled speed
    
    def set_traffic_mode(self, mode):
        """Set the traffic generation mode"""
        self.traffic_mode = mode
        # Reset traffic counts when mode changes
        self.traffic_counts = {direction: 0 for direction in self.traffic_counts}
        
    def get_traffic_counts(self):
        """Get current traffic counts by direction"""
        # Update counts based on waiting vehicles
        waiting = self.get_waiting_vehicles()
        self.traffic_counts = {
            'north': waiting[0],
            'south': waiting[1],
            'east': waiting[2],
            'west': waiting[3]
        }
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