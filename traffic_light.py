class TrafficLight:
    """
    Class to manage traffic light states and transitions.
    Handles the logic for traffic light changes and provides an interface for the RL agent.
    """
    
    def __init__(self):
        # Traffic light states
        self.NS_LIGHT = "green"  # North-South light (green, yellow, red)
        self.EW_LIGHT = "red"    # East-West light (red, yellow, green)
        
        # Yellow light transition counters
        self.NS_YELLOW_COUNTDOWN = 0
        self.EW_YELLOW_COUNTDOWN = 0
        
        # Minimum time between light changes (to prevent rapid switching)
        self.min_green_time = 30  # Ticks
        self.time_since_last_change = 0
        
        # Track current state for RL (0 = NS green/EW red, 1 = EW green/NS red)
        self.current_state = 0
    
    def update(self):
        """
        Update traffic light states based on countdown timers.
        Should be called every simulation tick.
        """
        self.time_since_last_change += 1
        
        # Handle yellow light transitions
        if self.NS_LIGHT == "yellow":
            self.NS_YELLOW_COUNTDOWN -= 1
            if self.NS_YELLOW_COUNTDOWN <= 0:
                self.NS_LIGHT = "red"
                self.EW_LIGHT = "green"  # Switch the other light to green
                self.current_state = 1
                self.time_since_last_change = 0
        
        if self.EW_LIGHT == "yellow":
            self.EW_YELLOW_COUNTDOWN -= 1
            if self.EW_YELLOW_COUNTDOWN <= 0:
                self.EW_LIGHT = "red"
                self.NS_LIGHT = "green"  # Switch the other light to green
                self.current_state = 0
                self.time_since_last_change = 0
    
    def set_state(self, state):
        """
        Set the traffic light state based on RL agent action.
        Only changes if minimum green time has elapsed.
        
        Args:
            state (int): 0 = NS green/EW red, 1 = EW green/NS red
        """
        # Only allow changes if minimum green time has elapsed
        if self.time_since_last_change < self.min_green_time:
            return False
        
        # If already in yellow transition, don't change
        if self.NS_LIGHT == "yellow" or self.EW_LIGHT == "yellow":
            return False
        
        # If already in the requested state, do nothing
        if (state == 0 and self.NS_LIGHT == "green") or (state == 1 and self.EW_LIGHT == "green"):
            return False
        
        # Initiate transition to new state via yellow
        if state == 0 and self.EW_LIGHT == "green":
            # Transition to NS green
            self.EW_LIGHT = "yellow"
            self.EW_YELLOW_COUNTDOWN = 30  # 1 second at 30 FPS
            return True
        
        elif state == 1 and self.NS_LIGHT == "green":
            # Transition to EW green
            self.NS_LIGHT = "yellow"
            self.NS_YELLOW_COUNTDOWN = 30  # 1 second at 30 FPS
            return True
        
        return False
    
    def get_state(self):
        """
        Get the current traffic light state.
        
        Returns:
            int: 0 = NS green/EW red, 1 = EW green/NS red
        """
        return self.current_state
    
    def get_light_states(self):
        """
        Get the current light states for both directions.
        
        Returns:
            tuple: (NS_LIGHT, EW_LIGHT)
        """
        return (self.NS_LIGHT, self.EW_LIGHT)
    
    def reset(self):
        """
        Reset traffic lights to initial state.
        """
        self.NS_LIGHT = "green"
        self.EW_LIGHT = "red"
        self.NS_YELLOW_COUNTDOWN = 0
        self.EW_YELLOW_COUNTDOWN = 0
        self.time_since_last_change = 0
        self.current_state = 0 