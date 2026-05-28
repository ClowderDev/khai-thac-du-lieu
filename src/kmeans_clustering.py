import sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import pandas as pd
from pathlib import Path

def normalize_features(df, features):
    # Min-max normalization to [0, 1] range
    df_norm = df.copy()
    norm_params = {}
    for col in features:
        # fill missing values
        df_norm[col] = df_norm[col].fillna(0.0)
        col_min = df_norm[col].min()
        col_max = df_norm[col].max()
        if col_max - col_min > 0:
            df_norm[col] = (df_norm[col] - col_min) / (col_max - col_min)
        else:
            df_norm[col] = 0.0
        norm_params[col] = {"min": float(col_min), "max": float(col_max)}
    return df_norm, norm_params

def kmeans(X, k, max_iters=100, seed=42):
    np.random.seed(seed)
    n_samples, n_features = X.shape
    
    # Initialize centroids: pick k random unique points from dataset
    random_indices = np.random.choice(n_samples, k, replace=False)
    centroids = X[random_indices].copy()
    
    prev_labels = np.zeros(n_samples)
    for _ in range(max_iters):
        # 1. Assignment step
        # compute distances from each point to all centroids
        distances = np.zeros((n_samples, k))
        for i in range(k):
            distances[:, i] = np.linalg.norm(X - centroids[i], axis=1)
            
        labels = np.argmin(distances, axis=1)
        
        # Check convergence
        if np.array_equal(labels, prev_labels):
            break
        prev_labels = labels
        
        # 2. Update step
        for i in range(k):
            points = X[labels == i]
            if len(points) > 0:
                centroids[i] = np.mean(points, axis=0)
            else:
                # If a centroid has no points, re-initialize it randomly
                centroids[i] = X[np.random.choice(n_samples)]
                
    # Calculate final WCSS (Within-Cluster Sum of Squares)
    wcss = 0.0
    for i in range(k):
        points = X[labels == i]
        if len(points) > 0:
            wcss += np.sum((points - centroids[i]) ** 2)
            
    return labels, centroids, float(wcss)

def run_kmeans_clustering(ward_df, k=3):
    features = [
        "GiaTrungBinh",
        "MatDoChungCu",
        "hospital_cnt",
        "mall_cnt",
        "metro_cnt",
        "university_cnt"
    ]
    
    # Clean and fill NaN values with 0
    df_clean = ward_df.copy()
    for col in features:
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0.0)
        
    df_norm, norm_params = normalize_features(df_clean, features)
    X = df_norm[features].values
    
    labels, centroids, wcss = kmeans(X, k, max_iters=100, seed=42)
    
    # Add cluster label to original dataframe
    df_clean["cluster_label"] = labels
    
    # Prepare results for export
    cluster_results = []
    for idx, row in df_clean.iterrows():
        cluster_results.append({
            "phuong": row["Phuong_xa"],
            "quan": row["Quan_huyen_goc"],
            "cluster": int(row["cluster_label"]),
            "values": {f: float(row[f]) for f in features}
        })
        
    # Format centroids (rescaled to original bounds)
    rescaled_centroids = []
    for i in range(k):
        c_vals = {}
        for idx, col in enumerate(features):
            min_val = norm_params[col]["min"]
            max_val = norm_params[col]["max"]
            rescaled_val = centroids[i][idx] * (max_val - min_val) + min_val
            c_vals[col] = float(rescaled_val)
        rescaled_centroids.append({
            "cluster": i,
            "centroid_values": c_vals,
            "normalized_values": [float(v) for v in centroids[i]]
        })
        
    results = {
        "wcss": wcss,
        "clusters": cluster_results,
        "centroids": rescaled_centroids,
        "features": features,
        "k": k
    }
    return results

if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    ward_df = pd.read_csv(ROOT / "phan_tich_theo_phuong_6_quan" / "mo_ta_thu_duc_theo_phuong.csv")
    results = run_kmeans_clustering(ward_df, k=3)
    
    print("K-Means Clustering completed.")
    print(f"WCSS: {results['wcss']:.3f}")
    
    # Print cluster counts
    counts = pd.Series([c['cluster'] for c in results['clusters']]).value_counts()
    print("Cluster sizes:")
    for cl, count in counts.items():
         print(f"  Cluster {cl}: {count} wards")
