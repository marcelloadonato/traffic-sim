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
- The simulation currently includes a basic vehicle model with north-to-south movement.
- Press the SPACE key to toggle the stoplight between red and green.

## Features
- Real-time visualization of traffic at a single intersection
- Vehicle agents with movement, waiting behavior, and satisfaction metrics
- Stoplight control (manual in MVP, to be replaced with RL)
- Basic metrics tracking (commute time, satisfaction) 