import random
import pygame
from config import WIDTH, HEIGHT, BUILDING_COLORS, DEBUG_MODE, SLOW_MODE, EPISODE_LENGTH, WHITE, BLACK, LANES
from visualization import draw_buildings, draw_road, draw_traffic_lights, draw_vehicle, draw_stats, draw_debug_info
from vehicle_spawner import generate_vehicle_spawn_schedule, spawn_vehicles
from collision import check_collision
from shared import get_screen, get_clock

class Simulation:
    def __init__(self):
        # Initialize buildings
        self.buildings = []
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
        self.episode_ended = False  # New flag to track episode state
    
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
        
    def set_data_recorder(self, data_recorder):
        """Set the data recorder for the simulation"""
        self.data_recorder = data_recorder
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Toggle lights
                    if self.ns_light == "green" and self.ew_light == "red":
                        self.ns_light = "yellow"
                        self.ns_yellow_countdown = 30  # 1 second at 30 FPS
                    elif self.ns_light == "red" and self.ew_light == "green":
                        self.ew_light = "yellow"
                        self.ew_yellow_countdown = 30
                elif event.key == pygame.K_d:  # Toggle debug mode
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
    
    def update_traffic_lights(self):
        """Update traffic light states"""
        if self.ns_light == "yellow":
            self.ns_yellow_countdown -= 1
            if self.ns_yellow_countdown <= 0:
                self.ns_light = "red"
                self.ew_light = "green"  # Switch the other light to green
        
        if self.ew_light == "yellow":
            self.ew_yellow_countdown -= 1
            if self.ew_yellow_countdown <= 0:
                self.ew_light = "red"
                self.ns_light = "green"  # Switch the other light to green
    
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
        # Get screen and fill it
        screen = get_screen()
        screen.fill(WHITE)
        
        # Draw everything
        draw_buildings(self.buildings)  # Pass buildings to draw_buildings
        draw_road()
        
        # Draw path indicators for better visibility
        if DEBUG_MODE:
            # Draw dots at all lane positions
            for lane, pos_data in LANES.items():
                pygame.draw.circle(screen, (255, 0, 0), pos_data['in'], 3)
                pygame.draw.circle(screen, (0, 0, 255), pos_data['out'], 3)
                
                # Draw queue positions
                for pos in pos_data['queue']:
                    pygame.draw.circle(screen, (0, 100, 0), pos, 2)
            
            # Draw dots at intersection
            pygame.draw.circle(screen, (255, 255, 0), (WIDTH//2, HEIGHT//2), 5)
        
        draw_traffic_lights(self.ns_light, self.ew_light)
        
        # Draw all vehicles
        for vehicle in self.active_vehicles:
            draw_vehicle(vehicle, DEBUG_MODE)
        
        # Calculate stats
        waiting_count = sum(1 for vehicle in self.active_vehicles if vehicle.state == "waiting")
        moving_count = sum(1 for vehicle in self.active_vehicles if vehicle.state == "moving")
        arrived_count = len(self.removed_vehicles)
        
        # Calculate average satisfaction
        if self.active_vehicles:
            avg_satisfaction = sum(vehicle.satisfaction for vehicle in self.active_vehicles) / len(self.active_vehicles)
        else:
            avg_satisfaction = 0
        
        # Draw stats and record data
        draw_stats(waiting_count, moving_count, arrived_count, avg_satisfaction, 
                  data_recorder.current_episode, self.current_tick)
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
        
        pygame.display.flip()
    
    def step(self, data_recorder):
        """Perform one step of the simulation"""
        self.handle_events()
        
        if not self.episode_ended:
            self.update_traffic_lights()
            
            # Spawn new vehicles if needed
            spawn_vehicles(self.current_tick, self.spawn_schedule, self.active_vehicles)
            
            # Update vehicles
            self.update_vehicles()
            
            # Increment tick counter
            self.current_tick += 1
            
            # Check if episode should end
            if self.current_tick >= EPISODE_LENGTH or (not self.active_vehicles and not self.spawn_schedule):
                # End episode
                data_recorder.end_episode()
                data_recorder.plot_learning_curve()
                self.episode_ended = True
                print("Episode ended automatically")
        
        # Draw everything
        self.draw(data_recorder)
        
        # Control simulation speed
        clock = get_clock()
        if SLOW_MODE:
            clock.tick(10)  # Slower for debugging
        else:
            clock.tick(30)  # Normal speed 