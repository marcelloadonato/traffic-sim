# Traffic Light Control with Reinforcement Learning

A traffic simulation that uses reinforcement learning to optimize traffic light timing at a single intersection. The RL agent learns to balance traffic flow efficiency with driver satisfaction.

## Features

- Real-time traffic simulation with vehicles of different types
- Reinforcement learning agent using PPO algorithm
- Interactive visualization with debug mode
- Educational tutorial mode
- Manual control mode for human experimentation
- RL dashboard showing agent's observations and decisions
- Score tracking and achievements
- Leaderboard of top performances

## How It Works

The RL agent observes the number of waiting vehicles in each direction and chooses traffic light states to optimize traffic flow. It earns rewards based on:
- Reducing average commute time (-0.2 * commute)
- Maintaining high driver satisfaction (+satisfaction)

The agent learns to balance these objectives through experience, improving its strategy over time.

## Controls

- `K_t`: Toggle tutorial mode (when not training)
- `K_m`: Toggle manual control mode (when not training)
- `K_SPACE`: Toggle traffic lights (in manual mode)
- `K_c`: Continue tutorial (in tutorial mode)
- `K_d`: Toggle debug mode
- `K_s`: Toggle slow mode
- `K_e`: End current episode
- `K_n`: Start new episode
- `K_t`: Start training (when not in tutorial mode)

## For Educators

This simulation is designed to help students understand:
1. How reinforcement learning can solve real-world problems
2. The trade-offs between traffic efficiency and driver satisfaction
3. The importance of state observation and reward design in RL

### Exercises

1. **Reward Function Exploration**
   - Adjust the reward weights in `traffic_env.py`
   - Compare the learning curves and traffic patterns
   - Discuss how different weights affect the agent's behavior

2. **Human vs RL Performance**
   - Use manual mode to optimize traffic flow
   - Compare your performance with the RL agent
   - Analyze what strategies work best

3. **State Space Design**
   - Modify the observation space in `traffic_env.py`
   - Add new features like vehicle types or queue lengths
   - Observe how different state representations affect learning

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the simulation:
   ```bash
   python main.py
   ```

## Requirements

- Python 3.8+
- Pygame
- NumPy
- Stable-Baselines3
- Pandas
- Matplotlib

## Project Structure

- `main.py`: Entry point and main game loop
- `src/`
  - `traffic_env.py`: RL environment definition
  - `simulation.py`: Core simulation logic
  - `rl_agent.py`: PPO agent implementation
  - `visualization.py`: Graphics and UI
  - `data_recorder.py`: Metrics and data logging
  - `vehicle.py`: Vehicle behavior
  - `config.py`: Configuration settings

## License

MIT License - feel free to use this project for educational purposes. 