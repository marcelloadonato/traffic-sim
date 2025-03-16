# traffic_env.py
# WARNING: This is a duplicate of src/traffic_env.py
# This file exists for backward compatibility only and delegates to the proper implementation

import warnings
warnings.warn(
    "You are using the root traffic_env.py file, which is deprecated. "
    "Please import from src.traffic_env instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export the actual implementation
from src.traffic_env import TrafficEnv

# For backward compatibility
if __name__ == "__main__":
    # If this file is run directly, it should behave the same as the src version
    print("Running traffic_env.py compatibility wrapper.")
    env = TrafficEnv()
    print("Environment created successfully.") 