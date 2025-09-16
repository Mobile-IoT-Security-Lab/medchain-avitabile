#!/usr/bin/env python3
"""
PRIN Demo Launcher
=======================

This script runs my demonstrations showing explicit before/after
redaction states as requested by the PRIN. It includes:

1. Standalone before/after redaction demo
2. my main simulation with improved output
3. Medical redaction demonstration
"""

import os
import sys
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def run_before_after_demo():
    """Run the my before/after redaction demonstration."""
    print_header("STANDALONE BEFORE/AFTER REDACTION DEMO")
    
    try:
        # Import and run the demo
        sys.path.insert(0, ROOT)
        from before_after_redaction_demo import run_comprehensive_before_after_demo
        
        results = run_comprehensive_before_after_demo()
        print(f"\n Demo completed successfully with {results['total_redactions']} redactions")
        return True
    except Exception as e:
        print(f" Error running before/after demo: {e}")
        return False

def run_medical_redaction_demo():
    """Run the medical redaction demonstration."""
    print_header("MEDICAL REDACTION DEMO (AVITABILE)")
    
    try:
        from avitabile_redaction_demo import run_avitabile_redaction_demo
        
        engine, rid_delete, rid_anon = run_avitabile_redaction_demo()
        print(f"\n Medical redaction demo completed successfully")
        print(f"  - DELETE request: {rid_delete}")
        print(f"  - ANONYMIZE request: {rid_anon}")
        return True
    except Exception as e:
        print(f" Error running medical redaction demo: {e}")
        return False

def run_my_main_simulation():
    """Run the main simulation with my before/after output."""
    print_header("ENHANCED MAIN SIMULATION WITH BEFORE/AFTER TRACKING")
    
    try:
        # Set environment to ensure redaction is enabled
        os.environ["TESTING_MODE"] = "1"
        
        # Import and run main
        from Main import main
        
        print("Running my simulation with explicit before/after redaction tracking...")
        main()
        print(f"\n my main simulation completed successfully")
        return True
    except Exception as e:
        print(f" Error running my main simulation: {e}")
        return False

def run_redactable_blockchain_demo():
    """Run the original redactable blockchain demo for comparison."""
    print_header("ORIGINAL REDACTABLE BLOCKCHAIN DEMO (FOR COMPARISON)")
    
    try:
        from redactable_blockchain_demo import run_demo
        
        run_demo()
        print(f"\n Original redactable blockchain demo completed successfully")
        return True
    except Exception as e:
        print(f" Error running original demo: {e}")
        return False

def main():
    """Run all demonstrations for the PRIN."""
    print_header("PRIN DEMONSTRATION - EXPLICIT BEFORE/AFTER REDACTION")
    print("This comprehensive demonstration shows blockchain redaction capabilities")
    print("with explicit before and after states as requested.")
    
    results = []
    
    # 1. Standalone before/after demo
    results.append(("Before/After Demo", run_before_after_demo()))
    
    # 2. Medical redaction demo
    results.append(("Medical Redaction Demo", run_medical_redaction_demo()))
    
    # 3. Original demo for comparison
    results.append(("Original Demo", run_redactable_blockchain_demo()))
    
    # 4. my main simulation
    results.append(("my Main Simulation", run_my_main_simulation()))
    
    # Summary
    print_header("DEMONSTRATION SUMMARY")
    
    successful = 0
    for name, success in results:
        status = " SUCCESS" if success else " FAILED"
        print(f"{name:.<50} {status}")
        if success:
            successful += 1
    
    print(f"\nCompleted {successful}/{len(results)} demonstrations successfully")
    
    if successful == len(results):
        print("\n All demonstrations completed successfully!")
        print("The PRIN can now see explicit before/after redaction states.")
    else:
        print(f"\n  {len(results) - successful} demonstration(s) failed.")
    
    print_header("FEATURES")
    print("1.  Explicit blockchain state before redaction operations")
    print("2.  Step-by-step redaction process visualization")
    print("3.  Comprehensive after-redaction state verification")
    print("4.  Hash preservation through chameleon hash forging")
    print("5.  Chain validity maintenance throughout operations")
    print("6.  Transaction modification and deletion capabilities")
    print("7.  Medical data redaction compliance (GDPR, HIPAA)")
    print("8.  Performance metrics and timing analysis")

if __name__ == "__main__":
    main()