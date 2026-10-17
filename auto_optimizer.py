#!/usr/bin/env /home/sim/alpaca_env/bin/python3
"""
DKF Model Self-Improver & Hyperparameter Optimizer
Optimizes DKF by adjusting covariance inflation factor to guide NEES towards [3.47, 4.57].
"""

import os
import json
import numpy as np
from simulation import Simulator

def main():
    exp_dir = "/home/sim/DKF_WSN_Experiment"
    print("=== STARTING DKF SELF-IMPROVER ===")

    # Target: We want NEES to lie in [3.47, 4.57]. Currently mean NEES is ~2.75 (underconfident/conservative).
    # We can inject a covariance inflation factor 'alpha' (0.5 to 1.5) to scale P or Q during prediction/update.
    # Let's find the best inflation factor to move the mean NEES close to the target center (4.0).
    
    best_alpha = 1.0
    best_dist = float('inf')
    best_rmse = float('inf')
    results = []

    # Test different covariance inflation factors
    for alpha in np.linspace(0.6, 1.4, 9):
        print(f"Testing Covariance Scale Alpha = {alpha:.2f}...")
        
        # Modify the simulator internally for testing (by overriding self.Q or scaling P in simulation loop)
        # To do this cleanly, we can scale Q in the simulator
        sim = Simulator(rs=28.0, seed=42)
        # Scale process noise covariance to adjust filter confidence
        sim.Q = sim.Q * alpha
        
        res = sim.run_monte_carlo(K=80, num_runs=20, L=5, p_loss=0.0, base_seed=4000)
        
        nees_matrix = np.array(res['nees_dkf'])
        mean_nees = np.mean(nees_matrix, axis=0)
        converged_nees = mean_nees[10:]
        avg_nees = np.mean(converged_nees)
        
        # Distance to ideal NEES center (4.0)
        dist_to_target = abs(avg_nees - 4.02) # (3.47 + 4.57)/2 = 4.02
        current_rmse = res['mean_rmse_dkf']
        
        print(f"  -> Average NEES: {avg_nees:.4f}, RMSE: {current_rmse:.4f} m, Dist to target: {dist_to_target:.4f}")
        
        results.append({
            'alpha': alpha,
            'avg_nees': avg_nees,
            'rmse': current_rmse,
            'dist': dist_to_target
        })
        
        if dist_to_target < best_dist:
            best_dist = dist_to_target
            best_alpha = alpha
            best_rmse = current_rmse

    print(f"\nOptimization complete! Best Covariance Scale Alpha: {best_alpha:.2f} (Dist: {best_dist:.4f}, RMSE: {best_rmse:.4f}m)")
    
    # Save the optimized config
    config = {
        'optimized_covariance_scale': best_alpha,
        'target_nees_range': [3.47, 4.57],
        'actual_optimized_avg_nees': float(np.mean([r['avg_nees'] for r in results if r['alpha'] == best_alpha])),
        'improvement_notes': "Adjusting process noise covariance Q scales filter confidence directly. A smaller Q makes the filter rely more on prediction, which decreases NEES if predictions are accurate."
    }
    
    with open(os.path.join(exp_dir, "optimized_config.json"), "w") as f:
        json.dump(config, f, indent=2)
        
    print("Optimized configuration saved to optimized_config.json.")

if __name__ == '__main__':
    main()
