from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from src.traffic_env import TrafficEnv
import numpy as np

"""
Traffic Light Control RL Agent using PPO (Proximal Policy Optimization)

Key Parameters:
- learning_rate=0.0003: Controls how fast the agent learns from experiences
- n_steps=2048: Number of steps to collect before updating the policy
- batch_size=64: Number of samples to process in each training batch
- n_epochs=10: Number of times to iterate over the collected data
- gamma=0.99: Discount factor for future rewards (higher = more future-focused)
- gae_lambda=0.95: Generalized Advantage Estimation parameter
- clip_range=0.2: Maximum allowed change in policy per update
"""

class TrafficRLAgent:
    def __init__(self, simulation_interface):
        """
        Initialize the RL agent for traffic light control.
        
        Args:
            simulation_interface: Interface to the traffic simulation
        """
        # Create the environment
        self.env = TrafficEnv(simulation_interface)
        self.env = DummyVecEnv([lambda: self.env])
        
        # Initialize the PPO agent
        self.model = PPO(
            "MlpPolicy",
            self.env,
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            verbose=1
        )
        
        # Training parameters
        self.total_timesteps = 2000  # Default training steps, will be overridden by UI
        self.eval_freq = 1000  # Evaluate every 1000 steps
        
    def train(self):
        """Train the RL agent"""
        print(f"Starting RL agent training for {self.total_timesteps} steps...")
        self.model.learn(
            total_timesteps=self.total_timesteps,
            progress_bar=True
        )
        print("Training completed!")
        
    def save(self, path):
        """Save the trained model"""
        self.model.save(path)
        print(f"Model saved to {path}")
        
    def load(self, path):
        """Load a trained model"""
        self.model = PPO.load(path, env=self.env)
        print(f"Model loaded from {path}")
        
    def predict(self, observation):
        """Get action prediction from the model"""
        action, _ = self.model.predict(observation, deterministic=True)
        return action 