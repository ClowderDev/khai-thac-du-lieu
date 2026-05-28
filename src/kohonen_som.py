import sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import pandas as pd
from pathlib import Path

def normalize_features(df, features):
    df_norm = df.copy()
    norm_params = {}
    for col in features:
        df_norm[col] = df_norm[col].fillna(0.0)
        col_min = df_norm[col].min()
        col_max = df_norm[col].max()
        if col_max - col_min > 0:
            df_norm[col] = (df_norm[col] - col_min) / (col_max - col_min)
        else:
            df_norm[col] = 0.0
        norm_params[col] = {"min": float(col_min), "max": float(col_max)}
    return df_norm, norm_params

def train_som(X, grid_size=10, epochs=100, alpha_0=0.5, radius_0=3, seed=42):
    np.random.seed(seed)
    n_samples, n_features = X.shape
    
    # 1. Initialize weights: 10x10 grid of neurons, each has n_features weights.
    # Initialize around 0.5 with random noise in [-0.1, 0.1] as described in slide 17
    weights = np.zeros((grid_size, grid_size, n_features))
    for i in range(grid_size):
        for j in range(grid_size):
            for k in range(n_features):
                val1 = np.random.randint(100) - 50.0
                val1 /= 500.0  # -0.1 to 0.1
                val2 = np.random.randint(100) - 50.0
                val2 /= 500.0  # -0.1 to 0.1
                weights[i, j, k] = 0.5 + (val1 * val2)
                
    # 2. Training loop
    for epoch in range(epochs):
        # Linear decay of learning rate and radius
        decay = 1.0 - (epoch / epochs)
        alpha = alpha_0 * decay
        radius = int(round(radius_0 * decay))
        
        # shuffle samples in each epoch
        indices = np.arange(n_samples)
        np.random.shuffle(indices)
        
        for idx in indices:
            sample = X[idx]
            
            # Step 2: Find Winning Neuron (BMU)
            # Calculate Euclidean distances to all neurons
            min_dist = float('inf')
            bmu_x, bmu_y = 0, 0
            
            for x in range(grid_size):
                for y in range(grid_size):
                    dist = np.linalg.norm(sample - weights[x, y])
                    if dist < min_dist:
                        min_dist = dist
                        bmu_x = x
                        bmu_y = y
                        
            # Step 3: Update weights of winning neuron and its neighborhood
            # Neighborhood range: ic-Nc(t) <= i <= ic+Nc(t)
            x_min = max(0, bmu_x - radius)
            x_max = min(grid_size - 1, bmu_x + radius)
            y_min = max(0, bmu_y - radius)
            y_max = min(grid_size - 1, bmu_y + radius)
            
            for x in range(x_min, x_max + 1):
                for y in range(y_min, y_max + 1):
                    # update weights: w(t+1) = w(t) + alpha * (sample - w(t))
                    weights[x, y] += alpha * (sample - weights[x, y])
                    
    return weights

def run_kohonen_som(ward_df, grid_size=10, epochs=100):
    features = [
        "GiaTrungBinh",
        "MatDoChungCu",
        "hospital_cnt",
        "mall_cnt",
        "metro_cnt",
        "university_cnt"
    ]
    
    df_clean = ward_df.copy()
    for col in features:
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0.0)
        
    df_norm, norm_params = normalize_features(df_clean, features)
    X = df_norm[features].values
    
    weights = train_som(X, grid_size, epochs)
    
    # Map each ward to its BMU coordinate on the grid
    mappings = []
    n_samples = len(df_clean)
    for idx in range(n_samples):
        row = df_clean.iloc[idx]
        sample = X[idx]
        
        min_dist = float('inf')
        bmu_x, bmu_y = 0, 0
        for x in range(grid_size):
            for y in range(grid_size):
                dist = np.linalg.norm(sample - weights[x, y])
                if dist < min_dist:
                    min_dist = dist
                    bmu_x = x
                    bmu_y = y
                    
        mappings.append({
            "phuong": row["Phuong_xa"],
            "quan": row["Quan_huyen_goc"],
            "bmu_x": int(bmu_x),
            "bmu_y": int(bmu_y),
            "distance": float(min_dist)
        })
        
    # Serialize weights for JSON export
    serialized_weights = []
    for x in range(grid_size):
        for y in range(grid_size):
            serialized_weights.append({
                "x": x,
                "y": y,
                "weights": [float(w) for w in weights[x, y]]
            })
            
    results = {
        "grid_size": grid_size,
        "mappings": mappings,
        "weights": serialized_weights,
        "features": features
    }
    return results

if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    ward_df = pd.read_csv(ROOT / "phan_tich_theo_phuong_6_quan" / "mo_ta_thu_duc_theo_phuong.csv")
    results = run_kohonen_som(ward_df, grid_size=10, epochs=100)
    
    print("Kohonen SOM completed.")
    print("Sample ward mapping on 10x10 grid:")
    for m in results["mappings"][:10]:
         print(f"  {m['phuong']} -> Grid({m['bmu_x']}, {m['bmu_y']})")
