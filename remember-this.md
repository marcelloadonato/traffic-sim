# Key Traffic Simulation Patterns

## Vehicle Collision Avoidance and Traffic Light Behavior

The successful vehicle behavior comes from three key components working together:

### 1. Precise Vehicle Position Tracking

```python
# In Vehicle class
def get_current_coords(self):
    """Get current coordinates based on position"""
    if isinstance(self.position, tuple):
        return self.position
    elif self.position == 'north':
        return (WIDTH//2, 0)
    elif self.position == 'south':
        return (WIDTH//2, HEIGHT)
    elif self.position == 'east':
        return (WIDTH, HEIGHT//2)
    elif self.position == 'west':
        return (0, HEIGHT//2)
    elif self.position == 'intersection':
        return (WIDTH//2, HEIGHT//2)
    return None
```

This provides exact coordinates for each position type, ensuring vehicles know exactly where they are.

### 2. Smart Collision Detection

```python
def is_behind(self, other_vehicle):
    """Check if this vehicle is behind another vehicle"""
    if not self.interpolated_position or not other_vehicle.interpolated_position:
        return False
    
    # Get current direction based on route
    current_idx = self.route.index(self.position)
    if current_idx >= len(self.route) - 1:
        return False
    
    next_pos = self.route[current_idx + 1]
    next_coords = self.get_next_coords(next_pos)
    if not next_coords:
        return False
    
    # Calculate direction vector
    dx = next_coords[0] - self.interpolated_position[0]
    dy = next_coords[1] - self.interpolated_position[1]
    
    # Get distance to other vehicle
    other_dx = other_vehicle.interpolated_position[0] - self.interpolated_position[0]
    other_dy = other_vehicle.interpolated_position[1] - self.interpolated_position[1]
    
    # Check if other vehicle is in our path and close enough to matter
    if abs(dx) > abs(dy):  # Moving horizontally
        if abs(other_dy) > 30:  # Not in same lane
            return False
        if dx > 0:  # Moving right
            return other_dx > 0 and other_dx < 100
        else:  # Moving left
            return other_dx < 0 and other_dx > -100
    else:  # Moving vertically
        if abs(other_dx) > 30:  # Not in same lane
            return False
        if dy > 0:  # Moving down
            return other_dy > 0 and other_dy < 100
        else:  # Moving up
            return other_dy < 0 and other_dy > -100
```

This collision detection is effective because it:
1. Checks if vehicles are in the same lane (within 30 pixels)
2. Only considers vehicles within 100 pixels ahead
3. Takes into account the actual direction of movement
4. Uses vector math to determine relative positions

### 3. Integrated Movement Logic

```python
# In Simulation.update_vehicles method
# Check if we need to stop
should_stop = False

# Stop at red or yellow light if approaching intersection
if vehicle.position in ['north', 'south', 'east', 'west'] and next_pos == 'intersection':
    ns_light, ew_light = light_state
    if ((vehicle.position in ['north', 'south'] and ns_light in ["red", "yellow"]) or
        (vehicle.position in ['east', 'west'] and ew_light in ["red", "yellow"])):
        should_stop = True
        vehicle.state = "waiting"
        vehicle.waiting_time += 1
        vehicle.speed = 0
        continue

# Check for vehicles ahead
if not should_stop:
    for other_vehicle in self.active_vehicles:
        if other_vehicle != vehicle and other_vehicle.state != "arrived":
            if vehicle.is_behind(other_vehicle):
                should_stop = True
                vehicle.state = "waiting"
                vehicle.waiting_time += 1
                vehicle.speed = 0
                break

# Update position if not stopped
if not should_stop:
    vehicle.state = "moving"
    vehicle.waiting_time = 0
    
    # Update position time
    vehicle.position_time += vehicle.speed
    
    # Calculate progress
    progress = min(vehicle.position_time / vehicle.position_threshold, 1.0)
    
    # Calculate new interpolated position
    new_x = current_coords[0] + (next_coords[0] - current_coords[0]) * progress
    new_y = current_coords[1] + (next_coords[1] - current_coords[1]) * progress
```

The movement logic works well because:
1. It checks traffic lights first
2. Then checks for vehicles ahead
3. Only updates position if both checks pass
4. Uses smooth interpolation between points
5. Maintains proper vehicle state ("waiting" vs "moving")
6. Tracks waiting time for metrics

## Key Insights

1. **Separation of Concerns**: Each component (position tracking, collision detection, movement) has a clear responsibility.
2. **Precise Coordinates**: Using exact coordinates rather than relative positions prevents position drift.
3. **Vector-Based Collision**: Using vector math for collision detection is more accurate than simple distance checks.
4. **State Management**: Clear state transitions (moving → waiting → moving) make behavior predictable.
5. **Proper Thresholds**: Using appropriate distance thresholds (30px for lane width, 100px for following distance) prevents unrealistic behavior. 