# traffic_env.py
import gym
import numpy as np
from gym import spaces

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
        # Apply the action to the simulation
        if self.simulation:
            self.simulation.set_traffic_lights(action)
            
            # Run simulation for a few ticks to see the effect
            for _ in range(10):  # Run for 10 ticks
                self.simulation.update_simulation()
        
        # Increment step counter
        self.current_step += 1
        
        # Get new observation
        observation = self._get_observation()
        
        # Calculate reward
        reward = self._calculate_reward()
        self.total_reward += reward
        
        # Check if episode is done
        done = self.current_step >= self.max_steps
        
        # If episode is done, record the total reward
        if done and self.simulation:
            self.episode_rewards.append(self.total_reward)
            
        # Additional info
        info = {
            'step': self.current_step,
            'waiting_vehicles': sum(observation),
            'avg_satisfaction': self.simulation.get_avg_satisfaction() if self.simulation else 0,
            'avg_commute_time': self.simulation.get_avg_commute_time() if self.simulation else 0
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
        
        # Apply the reward formula from the PRD
        reward = -0.1 * avg_commute_time + avg_satisfaction
        
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