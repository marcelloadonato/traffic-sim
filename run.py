#!/usr/bin/env python3
import sys
import os
import traceback

def main():
    try:
        # Add the project root directory to Python path for imports
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.append(project_root)
        
        # Import and run the main function
        from src.main import main
        main()
    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        print("\nDetailed error traceback:")
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"Error running the simulation: {e}")
        traceback.print_exc()
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 