import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os

# Set random seed generator helper
def get_rng(seed):
    return np.random.default_rng(seed)

class WSNEnvironment:
    def __init__(self, num_nodes=12, area_size=80.0, rc=40.0, seed=42):
        self.num_nodes = num_nodes
        self.area_size = area_size
        self.rc = rc
        rng = get_rng(seed)
        # Fixed node positions in 80x80 area
        self.node_positions = rng.uniform(5.0, area_size - 5.0, size=(num_nodes, 2))
        self.compute_adjacency_and_weights()

    def compute_adjacency_and_weights(self):
        N = self.num_nodes
        self.adj = np.zeros((N, N), dtype=int)
        self.dist_matrix = np.zeros((N, N))
        self.weights = np.zeros((N, N))
        
        for i in range(N):
            for j in range(N):
                if i != j:
                    d = np.linalg.norm(self.node_positions[i] - self.node_positions[j])
                    self.dist_matrix[i, j] = d
                    if d <= self.rc:
                        self.adj[i, j] = 1

        # Metropolis weights
        for i in range(N):
            neighbors = np.where(self.adj[i] == 1)[0]
            sum_w = 0.0
            for j in neighbors:
                # W_ij = 1 / (1 + max(deg_i, deg_j)) or max distance? 
                # Prompt says: W_{ij} = 1 / (1 + max(d_i, d_j)) where d_i is degree or distance? 
                # Let's check prompt: W_{ij} = 1 / (1 + max(d_i, d_j)) -> wait, d_i usually degree or distance? 
                # Let's re-read prompt: W_{ij} = 1 / (1 + max(d_i, d_j)). Let's interpret d_i as degree of node i (number of neighbors) or distance. 
                # Standard Metropolis-Hastings weights use degrees: W_ij = 1 / (1 + max(deg_i, deg_j)) for j in N_i. 
                # Let's use degree as standard Metropolis weight formula, or distance? Wait! "d_i" in graph theory notation often means degree, or let's support degree. Let's check standard Metropolis weights: W_ij = 1 / (1 + max(deg(i), deg(j))). Let's use degree.
                pass
            
        # Let's refine Metropolis weights using degrees:
        degrees = np.sum(self.adj, axis=1)
        for i in range(N):
            neighbors = np.where(self.adj[i] == 1)[0]
            for j in neighbors:
                # W_ij = 1 / (1 + max(deg_i, deg_j))
                self.weights[i, j] = 1.0 / (1.0 + max(degrees[i], degrees[j]))
            self.weights[i, i] = 1.0 - np.sum(self.weights[i])

    def generate_trajectory(self, K=80, seed=42):
        rng = get_rng(seed)
        T = 1.0
        F = np.array([[1, 0, T, 0],
                      [0, 1, 0, T],
                      [0, 0, 1, 0],
                      [0, 0, 0, 1]])
        Q_scale = 0.1
        Q = Q_scale * np.array([
            [T**3/3, 0, T**2/2, 0],
            [0, T**3/3, 0, T**2/2],
            [T**2/2, 0, T, 0],
            [0, T**2/2, 0, T]
        ])
        
        # Start near center, moving
        x = np.array([40.0, 40.0, 1.0, 0.5])
        traj = np.zeros((K, 4))
        for k in range(K):
            traj[k] = x
            w = rng.multivariate_normal(np.zeros(4), Q)
            x = F @ x + w
            # Keep inside bounds [0, 80] roughly by bouncing or just let it roam
        return traj

class Simulator:
    def __init__(self, num_nodes=12, area_size=80.0, rc=40.0, rs=28.0, sigma_r=1.0, seed=42):
        self.wsn = WSNEnvironment(num_nodes=num_nodes, area_size=area_size, rc=rc, seed=seed)
        self.rs = rs
        self.sigma_r = sigma_r
        self.R = np.diag([sigma_r**2, sigma_r**2])
        self.inv_R = np.linalg.inv(self.R)
        self.H = np.array([[1, 0, 0, 0],
                           [0, 1, 0, 0]])
        self.T = 1.0
        self.F = np.array([[1, 0, self.T, 0],
                           [0, 1, 0, self.T],
                           [0, 0, 1, 0],
                           [0, 0, 0, 1]])
        self.Q = 0.1 * np.array([
            [self.T**3/3, 0, self.T**2/2, 0],
            [0, self.T**3/3, 0, self.T**2/2],
            [self.T**2/2, 0, self.T, 0],
            [0, self.T**2/2, 0, self.T]
        ])

    def run_monte_carlo(self, K=80, num_runs=100, L=5, p_loss=0.0, base_seed=1000):
        N = self.wsn.num_nodes
        
        # Metrics storage
        rmse_ckf = np.zeros(K)
        rmse_lkf = np.zeros(K)
        rmse_dkf = np.zeros(K)
        
        nees_dkf = np.zeros((num_runs, K))
        
        for r in range(num_runs):
            run_seed = base_seed + r
            rng = get_rng(run_seed)
            true_traj = self.wsn.generate_trajectory(K=K, seed=run_seed)
            
            # Generate measurements and gamma for all nodes and time steps
            # z_i = H @ x + v_i
            measurements = np.zeros((K, N, 2))
            gamma = np.zeros((K, N), dtype=int)
            
            for k in range(K):
                for i in range(N):
                    v_i = rng.multivariate_normal(np.zeros(2), self.R)
                    measurements[k, i] = self.H @ true_traj[k] + v_i
                    dist = np.linalg.norm(self.wsn.node_positions[i] - true_traj[k][:2])
                    if dist <= self.rs:
                        gamma[k, i] = 1
                    else:
                        gamma[k, i] = 0
            
            # 1. Centralized KF (CKF)
            x_ckf = np.array([40.0, 40.0, 0.0, 0.0])
            P_ckf = np.eye(4) * 10.0
            
            # 2. Local KF (LKF) - Independent per node, average over nodes
            x_lkf = np.tile(np.array([40.0, 40.0, 0.0, 0.0]), (N, 1))
            P_lkf = np.tile(np.eye(4) * 10.0, (N, 1, 1))
            
            # 3. Distributed KF (DKF)
            x_dkf = np.tile(np.array([40.0, 40.0, 0.0, 0.0]), (N, 1))
            P_dkf = np.tile(np.eye(4) * 10.0, (N, 1, 1))
            
            run_rmse_c = np.zeros(K)
            run_rmse_l = np.zeros(K)
            run_rmse_d = np.zeros(K)
            
            for k in range(K):
                # --- CKF Step ---
                # Predict
                x_pred_c = self.F @ x_ckf
                P_pred_c = self.F @ P_ckf @ self.F.T + self.Q
                
                # Gather all active measurements
                active_nodes = np.where(gamma[k] == 1)[0]
                if len(active_nodes) > 0:
                    # Stack measurements
                    H_bar = np.kron(np.ones((len(active_nodes), 1)), self.H) # Actually stack H for each active node
                    # Better: stack rows
                    H_list = [self.H for _ in active_nodes]
                    H_stacked = np.vstack(H_list)
                    z_list = [measurements[k, i] for i in active_nodes]
                    z_stacked = np.concatenate(z_list)
                    R_list = [self.R for _ in active_nodes]
                    # Block diagonal R
                    from scipy.linalg import block_diag
                    R_stacked = block_diag(*R_list)
                    
                    S = H_stacked @ P_pred_c @ H_stacked.T + R_stacked
                    K_gain = P_pred_c @ H_stacked.T @ np.linalg.solve(S, np.eye(S.shape[0]))
                    x_ckf = x_pred_c + K_gain @ (z_stacked - H_stacked @ x_pred_c)
                    P_ckf = (np.eye(4) - K_gain @ H_stacked) @ P_pred_c
                else:
                    x_ckf = x_pred_c
                    P_ckf = P_pred_c
                
                pos_err_c = np.linalg.norm(x_ckf[:2] - true_traj[k][:2])
                run_rmse_c[k] = pos_err_c**2
                
                # --- LKF Step ---
                pos_err_l_sum = 0.0
                for i in range(N):
                    x_p = self.F @ x_lkf[i]
                    P_p = self.F @ P_lkf[i] @ self.F.T + self.Q
                    if gamma[k, i] == 1:
                        S_i = self.H @ P_p @ self.H.T + self.R
                        K_i = P_p @ self.H.T @ np.linalg.solve(S_i, np.eye(2))
                        x_lkf[i] = x_p + K_i @ (measurements[k, i] - self.H @ x_p)
                        P_lkf[i] = (np.eye(4) - K_i @ self.H) @ P_p
                    else:
                        x_lkf[i] = x_p
                        P_lkf[i] = P_p
                    pos_err_l_sum += np.linalg.norm(x_lkf[i][:2] - true_traj[k][:2])**2
                run_rmse_l[k] = pos_err_l_sum / N
                
                # --- DKF Step ---
                # 1. Prediction & Information form conversion
                Omega_pred = np.zeros((N, 4, 4))
                q_pred = np.zeros((N, 4))
                for i in range(N):
                    x_p = self.F @ x_dkf[i]
                    P_p = self.F @ P_dkf[i] @ self.F.T + self.Q
                    # Ensure symmetry and PD
                    P_p = 0.5 * (P_p + P_p.T)
                    try:
                        Omega_p = np.linalg.inv(P_p)
                    except:
                        Omega_p = np.linalg.pinv(P_p)
                    q_p = Omega_p @ x_p
                    
                    # Local measurement update
                    if gamma[k, i] == 1:
                        Omega_i = Omega_p + self.H.T @ self.inv_R @ self.H
                        q_i = q_p + self.H.T @ self.inv_R @ measurements[k, i]
                    else:
                        Omega_i = Omega_p
                        q_i = q_p
                    
                    Omega_pred[i] = Omega_i
                    q_pred[i] = q_i
                
                # 2. Consensus iterations (L rounds)
                Omega_curr = Omega_pred.copy()
                q_curr = q_pred.copy()
                
                for l_iter in range(L):
                    Omega_next = np.zeros_like(Omega_curr)
                    q_next = np.zeros_like(q_curr)
                    
                    for i in range(N):
                        neighbors = np.where(self.wsn.adj[i] == 1)[0]
                        # Effective weights with packet loss
                        # W_ii <- W_ii + sum of lost weights
                        w_self = self.wsn.weights[i, i]
                        sum_weighted_omega = w_self * Omega_curr[i]
                        sum_weighted_q = w_self * q_curr[i]
                        
                        for j in neighbors:
                            # Check packet loss from j to i
                            if p_loss > 0.0 and rng.random() < p_loss:
                                # Packet lost from j -> accumulate weight to self
                                w_self += self.wsn.weights[i, j]
                            else:
                                sum_weighted_omega += self.wsn.weights[i, j] * Omega_curr[j]
                                sum_weighted_q += self.wsn.weights[i, j] * q_curr[j]
                        
                        # If w_self changed due to packet loss, include self with updated w_self
                        if p_loss > 0.0 and w_self != self.wsn.weights[i, i]:
                            # Re-evaluate with updated w_self
                            sum_weighted_omega = w_self * Omega_curr[i]
                            sum_weighted_q = w_self * q_curr[i]
                            for j in neighbors:
                                if not (rng.random() < p_loss):
                                    sum_weighted_omega += self.wsn.weights[i, j] * Omega_curr[j]
                                    sum_weighted_q += self.wsn.weights[i, j] * q_curr[j]
                                    
                        Omega_next[i] = sum_weighted_omega
                        q_next[i] = sum_weighted_q
                        
                    Omega_curr = Omega_next
                    q_curr = q_next
                
                # 3. Recovery of state and covariance
                pos_err_d_sum = 0.0
                x_dkf_mean = np.zeros(4)
                for i in range(N):
                    Omega_i = 0.5 * (Omega_curr[i] + Omega_curr[i].T)
                    try:
                        P_i = np.linalg.inv(Omega_i)
                    except:
                        P_i = np.linalg.pinv(Omega_i)
                    x_i = P_i @ q_curr[i]
                    
                    P_dkf[i] = P_i
                    x_dkf[i] = x_i
                    x_dkf_mean += x_i
                    
                    pos_err_d_sum += np.linalg.norm(x_i[:2] - true_traj[k][:2])**2
                
                run_rmse_d[k] = pos_err_d_sum / N
                
                # Calculate NEES for DKF average state vs true state
                x_mean = x_dkf_mean / N
                # Average covariance across nodes
                P_mean = np.mean(P_dkf, axis=0)
                error_state = x_mean - true_traj[k]
                try:
                    nees_val = error_state.T @ np.linalg.solve(P_mean, error_state)
                except:
                    nees_val = error_state.T @ np.pinv(P_mean) @ error_state
                nees_dkf[r, k] = nees_val
            
            rmse_ckf += run_rmse_c
            rmse_lkf += run_rmse_l
            rmse_dkf += run_rmse_d
            
        rmse_ckf = np.sqrt(rmse_ckf / num_runs)
        rmse_lkf = np.sqrt(rmse_lkf / num_runs)
        rmse_dkf = np.sqrt(rmse_dkf / num_runs)
        
        return {
            'rmse_ckf': rmse_ckf,
            'rmse_lkf': rmse_lkf,
            'rmse_dkf': rmse_dkf,
            'nees_dkf': nees_dkf,
            'mean_rmse_ckf': np.mean(rmse_ckf),
            'mean_rmse_lkf': np.mean(rmse_lkf),
            'mean_rmse_dkf': np.mean(rmse_dkf),
        }

if __name__ == '__main__':
    print("Running DKF WSN Experiments...")
    sim = Simulator()
    res = sim.run_monte_carlo(K=80, num_runs=50, L=5, p_loss=0.0)
    print("Baseline run completed!")
    print(f"Mean RMSE CKF: {res['mean_rmse_ckf']:.4f}")
    print(f"Mean RMSE LKF: {res['mean_rmse_lkf']:.4f}")
    print(f"Mean RMSE DKF: {res['mean_rmse_dkf']:.4f}")
