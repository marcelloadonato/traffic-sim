# traffic_env.py
import gym
import numpy as np
from gym import spaces
from src.config import TOTAL_VEHICLES  # Fix import path

class TrafficEnv(gym.Env):
    """
    Custom Environment for traffic light control using reinforcement learning.
    This environment interfaces with the traffic simulation to optimize traffic flow.
    """
    metadata = {'render.modes': ['human']}

    def __init__(self, simulation_interface=None):
        super(TrafficEnv, self).__init__()
        
        # Reference to the simulation interface (will be set by main.py)
        self.simulation = simulation_interface
        
        # Define action space: 0 = NS green/EW red, 1 = EW green/NS red
        self.action_space = spaces.Discrete(2)
        
        # Define observation space: [north_waiting, south_waiting, east_waiting, west_waiting]
        # Each value represents the number of waiting vehicles in that direction (max 10)
        self.observation_space = spaces.Box(
            low=0, high=10, shape=(4,), dtype=np.int32
        )
        
        # Track episode stats
        self.current_step = 0
        self.max_steps = 1000  # Maximum steps per episode
        self.total_reward = 0
        self.episode_rewards = []
        
    def reset(self):
        """
        Reset the environment to start a new episode.
        Returns the initial observation.
        """
        # Reset the simulation
        if self.simulation:
            self.simulation.reset_simulation()
        
        # Reset episode tracking
        self.current_step = 0
        self.total_reward = 0
        
        # Get initial observation
        return self._get_observation()
    
    def step(self, action):
        """
        Take an action in the environment.
        
        Args:
            action (int): 0 = NS green/EW red, 1 = EW green/NS red
            
        Returns:
            observation (np.array): Current state observation
            reward (float): Reward for the action
            done (bool): Whether the episode is done
            info (dict): Additional information
        """
        if self.simulation:
            # Apply action and update simulation
            self.simulation.set_traffic_lights(action)
            self.simulation.update_simulation()
            
            # Calculate reward with stronger penalty for incomplete journeys
            avg_commute = self.simulation.get_avg_commute_time()
            avg_satisfaction = self.simulation.get_avg_satisfaction()
            
            # Increase penalty coefficient for commute time
            reward = -0.2 * avg_commute + avg_satisfaction  # Doubled penalty
            
            # Additional penalty if vehicles are stuck at episode end
            if self.simulation.episode_ended and self.simulation.active_vehicles:
                stuck_penalty = -10 * len(self.simulation.active_vehicles)
                reward += stuck_penalty
            
            observation = self._get_observation()
            done = self.simulation.episode_ended
            
            info = {
                'avg_satisfaction': avg_satisfaction,
                'avg_commute_time': avg_commute,
                'stuck_vehicles': len(self.simulation.active_vehicles)
            }
            
            return observation, reward, done, info
    
    def _get_observation(self):
        """
        Get the current state observation from the simulation.
        
        Returns:
            np.array: [north_waiting, south_waiting, east_waiting, west_waiting]
        """
        if not self.simulation:
            return np.zeros(4, dtype=np.int32)
        
        # Get waiting vehicle counts from each direction
        return np.array([
            self.simulation.get_waiting_count('north'),
            self.simulation.get_waiting_count('south'),
            self.simulation.get_waiting_count('east'),
            self.simulation.get_waiting_count('west')
        ], dtype=np.int32)
    
    def _calculate_reward(self):
        """
        Calculate the reward based on the current simulation state.
        Reward = -0.1 * avg_commute_time + avg_satisfaction
        
        Returns:
            float: The calculated reward
        """
        if not self.simulation:
            return 0.0
        
        avg_commute_time = self.simulation.get_avg_commute_time()
        avg_satisfaction = self.simulation.get_avg_satisfaction()
        
        # Exponentially increasing penalty for longer wait times
        time_penalty = sum(1.1 ** vehicle.commute_time for vehicle in self.simulation.active_vehicles)
        
        # Apply the reward formula from the PRD
        reward = avg_satisfaction - 0.01 * time_penalty
        
        return reward
    
    def render(self, mode='human'):
        """
        Render the environment.
        For this environment, rendering is handled by the simulation itself.
        """
        pass
    
    def close(self):
        """
        Close the environment.
        """
        pass 

    def calculate_reward(self):
        """Calculate the reward based on multiple metrics."""
        
        # Base metrics
        avg_commute = self.simulation.get_avg_commute_time()
        avg_satisfaction = self.simulation.get_avg_satisfaction()
        
        # Queue metrics
        queue_lengths = [self.simulation.get_waiting_count(d) for d in ['north', 'south', 'east', 'west']]
        max_queue = max(queue_lengths)
        queue_imbalance = max_queue - min(queue_lengths)
        
        # Throughput metrics
        completion_rate = len(self.simulation.removed_vehicles) / TOTAL_VEHICLES
        
        # Combined reward
        reward = (
            -0.1 * avg_commute +           # Time penalty
            1.0 * avg_satisfaction +        # Satisfaction
            -0.2 * max_queue +             # Queue length penalty
            -0.1 * queue_imbalance +       # Fairness penalty
            2.0 * completion_rate          # Completion bonus
        )
        
        return reward 