# traffic_env.py
import gym
import numpy as np

class TrafficEnv(gym.Env):
    def __init__(self, vehicles):
        """Initialize the traffic environment."""
        self.vehicles = vehicles  # List of Vehicle objects
        self.action_space = gym.spaces.Discrete(2)  # 0: NS green, 1: EW green
        self.observation_space = gym.spaces.Box(
            low=0, high=50, shape=(4,), dtype=np.float32  # Vehicles per approach
        )
        self.light_state = 0  # 0: NS green, 1: EW green

    def step(self, action):
        """Execute one simulation step."""
        self.light_state = action
        # Update all vehicles
        for vehicle in self.vehicles:
            vehicle.update("green" if self.light_state == 0 else "red")
        # Calculate state and reward
        state = self.get_state()
        reward = self.get_reward()
        done = all(v.state == "arrived" for v in self.vehicles)
        return state, reward, done, {}

    def reset(self):
        """Reset the environment."""
        self.light_state = 0
        for vehicle in self.vehicles:
            vehicle.__init__(vehicle.position, vehicle.destination)
        return self.get_state()

    def get_state(self):
        """Return current traffic state."""
        # For MVP, count vehicles waiting at intersection (simplified)
        waiting = sum(1 for v in self.vehicles if v.state == "waiting")
        return np.array([waiting, 0, 0, 0])  # Placeholder for 4 approaches

    def get_reward(self):
        """Calculate reward based on commute time and satisfaction."""
        avg_commute = np.mean([v.commute_time for v in self.vehicles])
        avg_satisfaction = np.mean([v.satisfaction for v in self.vehicles])
        return -0.1 * avg_commute + avg_satisfaction 