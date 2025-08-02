#!/usr/bin/env python3
"""
Run script for the Redactable Blockchain Benchmarks project.
This script properly initializes the configuration before running the simulation.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and initialize the configuration
from InputsConfig import InputsConfig as p

def main():
    print("=== Redactable Blockchain Benchmarks ===")
    print()
    
    # Ask user for configuration
    print("Choose simulation mode:")
    print("1. Testing mode (faster, smaller network)")
    print("2. Full simulation mode (slower, larger network)")
    choice = input("Enter your choice (1 or 2): ").strip()
    
    testing_mode = choice == "1"
    
    # Initialize configuration
    print(f"Initializing configuration in {'testing' if testing_mode else 'full'} mode...")
    p.initialize(testing_mode=testing_mode)
    
    print(f"Configuration loaded:")
    print(f"- Number of nodes: {p.NUM_NODES}")
    print(f"- Simulation time: {p.simTime} seconds")
    print(f"- Block interval: {p.Binterval} seconds")
    print(f"- Transaction rate: {p.Tn} tx/sec")
    print()
    
    # Import and run the main simulation
    from Main import main as run_simulation
    
    print("Starting simulation...")
    run_simulation()

if __name__ == "__main__":
    main()
