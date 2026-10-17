#!/usr/bin/env /home/sim/alpaca_env/bin/python3
"""
DKF WSN Full Experiment Suite & Automated Optimizer
Runs Monte Carlo simulations for KB1 and KB2, saves results as JSON,
generates publication-quality plots, and writes the Obsidian-ready research report.
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from simulation import Simulator

def main():
    exp_dir = "/home/sim/DKF_WSN_Experiment"
    os.makedirs(exp_dir, exist_ok=True)
    os.makedirs(os.path.join(exp_dir, "plots"), exist_ok=True)

    print("=== STARTING DKF WSN EXPERIMENT SUITE ===")

    # ----------------------------------------------------
    # KỊCH BẢN 1 (KB1): Quét Rs in {60, 28} và L in {1, 2, 3, 5, 10}
    # ----------------------------------------------------
    print("\n--- Running Scenario 1 (KB1) ---")
    rs_list = [60.0, 28.0]
    l_list = [1, 2, 3, 5, 10]
    
    kb1_results = {}
    
    for rs in rs_list:
        kb1_results[str(rs)] = {}
        for l in l_list:
            print(f"-> Simulating Rs={rs}m, L={l}...")
            sim = Simulator(rs=rs, seed=42)
            # Run 50 Monte Carlo runs for speed/stability tradeoff (can scale to 100)
            res = sim.run_monte_carlo(K=80, num_runs=50, L=l, p_loss=0.0, base_seed=2000)
            
            kb1_results[str(rs)][str(l)] = {
                'mean_rmse_ckf': float(res['mean_rmse_ckf']),
                'mean_rmse_lkf': float(res['mean_rmse_lkf']),
                'mean_rmse_dkf': float(res['mean_rmse_dkf']),
                'rmse_ckf': res['rmse_ckf'].tolist(),
                'rmse_lkf': res['rmse_lkf'].tolist(),
                'rmse_dkf': res['rmse_dkf'].tolist(),
                'nees_dkf': res['nees_dkf'].tolist()
            }

    # Save KB1 results
    with open(os.path.join(exp_dir, "kb1_results.json"), "w") as f:
        json.dump(kb1_results, f, indent=2)
    print("KB1 completed and saved to kb1_results.json")

    # ----------------------------------------------------
    # KỊCH BẢN 2 (KB2): Cố định Rs=28m, L=5, quét p_loss in {0, 10, 20, 30}%
    # ----------------------------------------------------
    print("\n--- Running Scenario 2 (KB2) ---")
    ploss_list = [0.0, 0.1, 0.2, 0.3]
    kb2_results = {}
    
    for pl in ploss_list:
        print(f"-> Simulating Packet Loss = {int(pl*100)}%...")
        sim = Simulator(rs=28.0, seed=42)
        res = sim.run_monte_carlo(K=80, num_runs=50, L=5, p_loss=pl, base_seed=3000)
        
        kb2_results[str(pl)] = {
            'mean_rmse_dkf': float(res['mean_rmse_dkf']),
            'rmse_dkf': res['rmse_dkf'].tolist(),
            'nees_dkf': res['nees_dkf'].tolist()
        }

    with open(os.path.join(exp_dir, "kb2_results.json"), "w") as f:
        json.dump(kb2_results, f, indent=2)
    print("KB2 completed and saved to kb2_results.json")

    # ----------------------------------------------------
    # PLOTTING RESULTS
    # ----------------------------------------------------
    print("\n--- Generating Publication-Quality Plots ---")
    
    # 1. Plot RMSE vs Time for Rs=28m, L=5 (CKF vs LKF vs DKF)
    plt.figure(figsize=(10, 6))
    time_axis = np.arange(1, 81)
    # Extract from kb1_results for Rs=28, L=5
    # Wait, let's load or grab directly from sim run or JSON
    with open(os.path.join(exp_dir, "kb1_results.json"), "r") as f:
        data_kb1 = json.load(f)
    
    rmse_c = data_kb1["28.0"]["5"]["rmse_ckf"]
    rmse_l = data_kb1["28.0"]["5"]["rmse_lkf"]
    rmse_d = data_kb1["28.0"]["5"]["rmse_dkf"]
    
    plt.plot(time_axis, rmse_c, 'k--', label='Centralized KF (CKF)', linewidth=2)
    plt.plot(time_axis, rmse_l, 'r-.', label='Local KF (LKF, Rs=28m)', linewidth=2)
    plt.plot(time_axis, rmse_d, 'b-', label='Distributed KF (DKF, L=5, Rs=28m)', linewidth=2)
    plt.xlabel('Thời gian (Bước k)', fontsize=12)
    plt.ylabel('RMSE vị trí trung bình (m)', fontsize=12)
    plt.title('So sánh sai số bám vết (RMSE) giữa CKF, LKF và DKF (Rs = 28m)', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(exp_dir, "plots", "rmse_comparison_rs28.png"), dpi=300)
    plt.close()

    # 2. Plot RMSE vs L for Rs=28m
    plt.figure(figsize=(9, 5))
    l_vals = [1, 2, 3, 5, 10]
    mean_rmse_l_vals = [data_kb1["28.0"][str(l)]["mean_rmse_dkf"] for l in l_vals]
    ckf_baseline = data_kb1["28.0"]["5"]["mean_rmse_ckf"]
    lkf_baseline = data_kb1["28.0"]["5"]["mean_rmse_lkf"]
    
    plt.plot(l_vals, mean_rmse_l_vals, 'bo-', label='DKF (Rs=28m)', linewidth=2, markersize=8)
    plt.axhline(y=ckf_baseline, color='k', linestyle='--', label=f'CKF Cận tối ưu ({ckf_baseline:.2f}m)')
    plt.axhline(y=lkf_baseline, color='r', linestyle=':', label=f'LKF Đơn lẻ ({lkf_baseline:.2f}m)')
    plt.xlabel('Số vòng đồng thuận L', fontsize=12)
    plt.ylabel('RMSE vị trí trung bình toàn cục (m)', fontsize=12)
    plt.title('Ảnh hưởng của số vòng đồng thuận L đến sai số ước lượng DKF', fontsize=14, fontweight='bold')
    plt.xticks(l_vals)
    plt.legend(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(exp_dir, "plots", "rmse_vs_consensus_L.png"), dpi=300)
    plt.close()

    # 3. Plot NEES over time with 95% confidence bounds
    plt.figure(figsize=(10, 5))
    nees_matrix = np.array(data_kb1["28.0"]["5"]["nees_dkf"]) # shape (num_runs, K)
    mean_nees = np.mean(nees_matrix, axis=0)
    
    plt.plot(time_axis, mean_nees, 'b-', label='NEES trung bình (DKF)', linewidth=2)
    plt.axhline(y=3.47, color='g', linestyle='--', label='Ngưỡng dưới 95% (3.47)')
    plt.axhline(y=4.57, color='g', linestyle='--', label='Ngưỡng trên 95% (4.57)')
    plt.xlabel('Thời gian (Bước k)', fontsize=12)
    plt.ylabel('Giá trị NEES trung bình', fontsize=12)
    plt.title('Kiểm định tính nhất quán NEES của DKF (Rs = 28m, L = 5)', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(1.0, 8.0)
    plt.tight_layout()
    plt.savefig(os.path.join(exp_dir, "plots", "nees_consistency_check.png"), dpi=300)
    plt.close()

    # 4. Plot Packet Loss impact (KB2)
    plt.figure(figsize=(9, 5))
    with open(os.path.join(exp_dir, "kb2_results.json"), "r") as f:
        data_kb2 = json.load(f)
    
    ploss_keys = [0.0, 0.1, 0.2, 0.3]
    ploss_rmse = [data_kb2[str(pl)]["mean_rmse_dkf"] for pl in ploss_keys]
    
    plt.plot([p*100 for p in ploss_keys], ploss_rmse, 'ms-', linewidth=2, markersize=8)
    plt.xlabel('Tỷ lệ mất gói tin P_loss (%)', fontsize=12)
    plt.ylabel('RMSE vị trí trung bình (m)', fontsize=12)
    plt.title('Ảnh hưởng của tỷ lệ mất gói tin kênh truyền đến độ chính xác DKF', fontsize=14, fontweight='bold')
    plt.xticks([0, 10, 20, 30])
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(exp_dir, "plots", "packet_loss_impact.png"), dpi=300)
    plt.close()

    print("All plots generated successfully in /home/sim/DKF_WSN_Experiment/plots/")

if __name__ == '__main__':
    main()
