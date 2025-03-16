from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from src.traffic_env import TrafficEnv
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QMutex

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

class TrainingThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, model, total_timesteps, callback):
        super().__init__()
        self.model = model
        self.total_timesteps = total_timesteps
        self.callback = callback
        
    def run(self):
        try:
            self.model.learn(
                total_timesteps=self.total_timesteps,
                progress_bar=True,
                callback=self.callback
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class TrafficRLAgent(QObject):
    # Signals for visualization updates
    traffic_update = pyqtSignal(dict)  # Emits traffic counts by direction
    reward_update = pyqtSignal(int, float)  # Emits (step, reward)
    training_finished = pyqtSignal()
    training_error = pyqtSignal(str)
    
    def __init__(self, simulation_interface):
        """
        Initialize the RL agent for traffic light control.
        
        Args:
            simulation_interface: Interface to the traffic simulation
        """
        super().__init__()
        
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
        self.total_timesteps = 2000  # Default training steps
        self.eval_freq = 1000  # Evaluate every 1000 steps
        self.is_training = False
        self.training_thread = None
        self.mutex = QMutex()  # For thread-safe operations
        
    def train(self):
        """Train the RL agent in a separate thread"""
        if self.is_training:
            return
            
        print(f"Starting RL agent training for {self.total_timesteps} steps...")
        self.is_training = True
        
        # Custom callback for visualization
        def callback(locals, globals):
            if not self.is_training:
                return False
                
            try:
                # Get current traffic counts
                traffic_counts = self.env.get_attr('simulation')[0].get_traffic_counts()
                self.traffic_update.emit(traffic_counts)
                
                # Get current reward
                current_step = locals.get('num_timesteps', 0)
                current_reward = locals.get('rewards', [0])[0]
                self.reward_update.emit(current_step, current_reward)
                
                return True
            except Exception as e:
                print(f"Error in callback: {str(e)}")
                return False
        
        # Create and start training thread
        self.training_thread = TrainingThread(self.model, self.total_timesteps, callback)
        self.training_thread.finished.connect(self.on_training_finished)
        self.training_thread.error.connect(self.on_training_error)
        self.training_thread.start()
        
    def on_training_finished(self):
        """Handle training completion"""
        self.mutex.lock()
        self.is_training = False
        self.mutex.unlock()
        print("Training completed!")
        self.training_finished.emit()
        
    def on_training_error(self, error_msg):
        """Handle training errors"""
        self.mutex.lock()
        self.is_training = False
        self.mutex.unlock()
        print(f"Training error: {error_msg}")
        self.training_error.emit(error_msg)
        
    def stop_training(self):
        """Stop the training process"""
        self.mutex.lock()
        self.is_training = False
        self.mutex.unlock()
        if self.training_thread and self.training_thread.isRunning():
            self.training_thread.terminate()
            self.training_thread.wait()
        
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