# traffic_env.py
import gymnasium as gym
import numpy as np
from gymnasium import spaces
from src.config import TOTAL_VEHICLES

"""
Custom Environment for traffic light control using reinforcement learning.
This environment interfaces with the traffic simulation to optimize traffic flow.

Key Components:
- Observation: Number of waiting vehicles per direction (state for RL)
- Action: 0 = NS green/EW red, 1 = EW green/NS red (what RL controls)
- Reward: -0.2 * commute + satisfaction balances efficiency and happiness
"""

class TrafficEnv(gym.Env):
    metadata = {'render_modes': ['human']}

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
        
    def reset(self, seed=None):
        """
        Reset the environment to start a new episode.
        Returns the initial observation.
        """
        super().reset(seed=seed)
        
        # Reset the simulation
        if self.simulation:
            self.simulation.reset()
        
        # Reset episode tracking
        self.current_step = 0
        self.total_reward = 0
        
        # Get initial observation
        return self._get_observation(), {}
    
    def step(self, action):
        """
        Take an action in the environment.
        
        Args:
            action (int): 0 = NS green/EW red, 1 = EW green/NS red
            
        Returns:
            observation (np.array): Current state observation
            reward (float): Reward for the action
            terminated (bool): Whether the episode is done
            truncated (bool): Whether the episode was truncated
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
            reward = -0.2 * avg_commute + avg_satisfaction
            
            # Additional penalty if vehicles are stuck at episode end
            if self.simulation.episode_ended and self.simulation.active_vehicles:
                stuck_penalty = -10 * len(self.simulation.active_vehicles)
                reward += stuck_penalty
            
            observation = self._get_observation()
            terminated = self.simulation.episode_ended
            truncated = self.current_step >= self.max_steps
            
            info = {
                'avg_satisfaction': avg_satisfaction,
                'avg_commute_time': avg_commute,
                'stuck_vehicles': len(self.simulation.active_vehicles)
            }
            
            return observation, reward, terminated, truncated, info
    
    def _get_observation(self):
        """Get the current observation state"""
        waiting_vehicles = self.simulation.get_waiting_vehicles()
        return np.array([
            waiting_vehicles['north'],
            waiting_vehicles['south'],
            waiting_vehicles['east'],
            waiting_vehicles['west']
        ]) 