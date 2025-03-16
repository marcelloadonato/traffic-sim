import random
import pygame
import numpy as np
from config import WIDTH, HEIGHT, BUILDING_COLORS, DEBUG_MODE, SLOW_MODE, EPISODE_LENGTH, WHITE, BLACK, LANES, SPEED_SLIDER, TRAINING_SLIDER
from visualization import draw_buildings, draw_road, draw_traffic_lights, draw_vehicle, draw_stats, draw_debug_info, draw_speed_slider, draw_training_slider
from vehicle_spawner import generate_vehicle_spawn_schedule, spawn_vehicles
from collision import check_collision
from shared import get_screen, get_clock
from rl_agent import TrafficRLAgent

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
        else:  # EW green
            if self.ns_light == "green":
                self.ns_light = "yellow"
                self.ns_yellow_countdown = 30
                self.light_change_count += 1
    
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
        
        if self.ew_light == "yellow":
            self.ew_yellow_countdown -= 1
            if self.ew_yellow_countdown <= 0:
                self.ew_light = "red"
                self.ns_light = "green"
                self.light_change_count += 1
    
    def update_vehicles(self):
        """Update all active vehicles"""
        for vehicle in self.active_vehicles[:]:  # Use a copy for safe iteration
            # Set the collision detection function
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
    
    def step(self, data_recorder):
        """Update simulation state"""
        # Handle events first
        self.handle_events()
        
        if not self.episode_ended:
            # Handle tutorial mode pauses
            if self.tutorial_mode and self.current_tick % 100 == 0:
                return  # Pause for tutorial message
            
            # Update simulation state
            self.update_traffic_lights()
            
            # Spawn new vehicles if needed
            spawn_vehicles(self.current_tick, self.spawn_schedule, self.active_vehicles)
            
            # Update vehicles
            self.update_vehicles()
            
            # Increment tick counter
            self.current_tick += 1
            
            # Check for episode end
            if self.current_tick >= EPISODE_LENGTH or (not self.active_vehicles and not self.spawn_schedule):
                self.episode_ended = True
                if hasattr(self, 'data_recorder'):
                    self.data_recorder.end_episode(self.light_change_count)
        
        # Draw current state
        self.draw(data_recorder)
        
        # Control simulation speed using the slider
        clock = get_clock()
        if SLOW_MODE:
            clock.tick(10)  # Slower for debugging
        else:
            clock.tick(self.current_fps)  # Use slider-controlled speed 