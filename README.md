# Traffic Simulation with Reinforcement Learning

A project to demonstrate RL-based traffic optimization in a virtual town.

## Setup Instructions
1. Clone this repository or create the project folder `traffic-sim-mvp`.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the simulation:
   ```
   python main.py
   ```

## Project Status
- MVP: Single intersection with 20–50 agents and one stoplight.
- The simulation includes a basic vehicle model with various movement patterns.
- Reinforcement Learning (RL) agent controls the traffic light to optimize flow.

## Features
- Real-time visualization of traffic at a single intersection
- Vehicle agents with movement, waiting behavior, and satisfaction metrics
- Stoplight control with RL-based optimization
- Basic metrics tracking (commute time, satisfaction)

## Controls
- **T**: Start RL agent training (learn optimal stoplight control)
- **D**: Toggle debug mode to display additional information
- **S**: Toggle slow mode for easier debugging
- **E**: End the current episode manually
- **N**: Start a new episode (after one has ended)
- **Speed Slider**: Adjust simulation speed with the slider at the bottom
- **Training Steps Slider**: Adjust the number of training steps (100-20,000) before pressing T

## Reinforcement Learning
The RL agent observes the number of waiting vehicles in each direction and learns to control the traffic light to minimize commute times and maximize vehicle satisfaction.

The agent uses Proximal Policy Optimization (PPO) algorithm from Stable Baselines3 for training.

## Requirements
- Python 3.8+
- PyGame
- NumPy
- Pandas
- Matplotlib
- Stable Baselines3
- Gymnasium 