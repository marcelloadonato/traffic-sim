# Cursor Rules for Traffic Simulation Project

## Project Focus and Scope
- Prioritize the Minimum Viable Product (MVP): a single-intersection traffic simulation with 20–50 agents and one stoplight. Avoid suggesting features beyond this unless explicitly requested.

## Educational Clarity
- Include explanations for complex operations (e.g., RL setup, simulation logic) in code suggestions. Prefer readable code over concise shortcuts.  
  - Example: For Gym environment setup, comment what state, action, and reward mean.

## Technical Stack Adherence
- Use only these libraries unless directed otherwise:  
  - Simulation: Custom Python code (NetworkX optional for future road networks).  
  - Reinforcement Learning: Gym (environments), Stable Baselines3 (RL algorithms).  
  - Visualization: Pygame (2D rendering).  
  - Data Analysis: Pandas (metrics logging), Matplotlib (plotting).

## Modularity and Extensibility
- Suggest modular code structures that can expand later (e.g., to multiple intersections).  
  - Example: Define agents and stoplights as classes with reusable interfaces.

## Performance Considerations
- Optimize for high-end consumer hardware (e.g., quad-core CPU, 16GB RAM). Recommend efficient algorithms/data structures for agent movement and updates.  
  - Example: Use lists or NumPy arrays for agent positions.

## Debugging and Logging
- Encourage detailed logging of events (agent actions, stoplight changes, RL decisions) via print statements or files.  
  - Example: Log "Vehicle 12 stopped at light" or "Light turned green at tick 50".

## Visualization Guidance
- Assist with Pygame setup for real-time 2D rendering using simple visuals (e.g., dots for agents, rectangles for roads).

## Metrics and Analysis
- Guide tracking of metrics (commute time, satisfaction) with Pandas and plotting with Matplotlib post-simulation.

## Reinforcement Learning Best Practices
- Explain RL basics (state, action, reward) in suggestions. Start with simple reward functions and suggest refinements later.  
  - Example: Begin with reward based on waiting vehicles, adjust based on results.

## Documentation and Comments
- Add comments to code suggestions, especially for RL, agent behavior, and simulation steps. Prompt updates to the PRD or README for new decisions.