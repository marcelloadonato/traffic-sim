# Traffic Light Control with Reinforcement Learning

A traffic simulation that uses reinforcement learning to optimize traffic light timing at a single intersection. The RL agent learns to balance traffic flow efficiency with driver satisfaction.

## Features

- Real-time traffic simulation with vehicles of different types
- Reinforcement learning agent using PPO algorithm
- Interactive visualization with debug mode
- Educational tutorial mode with step-by-step explanations
- Manual control mode for human experimentation
- RL dashboard showing agent's observations and decisions
- Score tracking and achievements
- Leaderboard of top performances
- Multiple traffic generation modes (Random, Rush Hour, Custom)
- Real-time performance metrics and statistics
- CUDA support for faster training
- Collision detection and prevention
- Vehicle spawn scheduling system
- Building generation for realistic urban environment

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
- `K_r`: Toggle between traffic generation modes (Random/Rush Hour/Custom)
- `K_1`-`K_4`: Adjust simulation speed (1x-4x)
- `K_ESCAPE`: Quit simulation

## Simulation Modes

1. **RL Mode (Default)**
   - AI agent controls traffic lights
   - Real-time learning and optimization
   - Performance metrics displayed

2. **Manual Mode**
   - Human control of traffic lights
   - Space bar to toggle lights
   - Compare performance with AI

3. **Tutorial Mode**
   - Step-by-step learning experience
   - Explains key concepts
   - Interactive demonstrations

4. **Debug Mode**
   - Shows detailed simulation information
   - Vehicle states and positions
   - Performance metrics

## Traffic Generation Modes

1. **Random Mode**
   - Random vehicle spawning
   - Balanced traffic distribution

2. **Rush Hour Mode**
   - Increased traffic density
   - Directional traffic patterns
   - Realistic peak hour simulation

3. **Custom Mode**
   - Configurable traffic patterns
   - Adjustable spawn rates
   - Direction-specific traffic

## For Educators

This simulation is designed to help students understand:
1. How reinforcement learning can solve real-world problems
2. The trade-offs between traffic efficiency and driver satisfaction
3. The importance of state observation and reward design in RL
4. Traffic flow dynamics and optimization
5. Real-world applications of AI in urban planning

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

4. **Traffic Pattern Analysis**
   - Experiment with different traffic generation modes
   - Analyze how traffic patterns affect performance
   - Design custom traffic scenarios

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
- PyTorch (with CUDA support if available)

## Project Structure

- `main.py`: Entry point and main game loop
- `src/`
  - `traffic_env.py`: RL environment definition
  - `simulation.py`: Core simulation logic
  - `rl_agent.py`: PPO agent implementation
  - `visualization.py`: Graphics and UI
  - `data_recorder.py`: Metrics and data logging
  - `vehicle.py`: Vehicle behavior
  - `vehicle_spawner.py`: Traffic generation system
  - `collision.py`: Collision detection
  - `config.py`: Configuration settings
  - `shared.py`: Shared utilities and constants

## License

MIT License - feel free to use this project for educational purposes. 