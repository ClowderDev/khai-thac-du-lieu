import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Import our custom modules
from data_preprocessing import preprocess_data
from apriori import run_apriori_on_apartments
from rough_set import run_rough_set_analysis
from decision_tree_id3 import run_id3_decision_tree
from naive_bayes import run_naive_bayes_classification
from kmeans_clustering import run_kmeans_clustering
from kohonen_som import run_kohonen_som

def zscore(series):
    mean_val = series.mean()
    sd_val = series.std()
    if pd.isna(sd_val) or sd_val == 0:
        return pd.Series(0.0, index=series.index)
    return (series - mean_val) / sd_val

def compute_potential_score(ward_df, apartment_df):
    # Calculate average distance to POIs per ward
    dist_ward = apartment_df.groupby(["Quan_huyen_goc", "Phuong_xa"])[[
        "dist_hospital_m", "dist_mall_m", "dist_metro_m", "dist_university_m"
    ]].mean().reset_index()
    
    potential_df = ward_df.merge(dist_ward, on=["Quan_huyen_goc", "Phuong_xa"], how="left")
    
    # Fill missing values
    fill_cols = [
        "GiaTrungBinh", "MatDoChungCu", "hospital_cnt", "mall_cnt", "metro_cnt", "university_cnt",
        "dist_hospital_m", "dist_mall_m", "dist_metro_m", "dist_university_m"
    ]
    for col in fill_cols:
        potential_df[col] = potential_df[col].fillna(0.0)
        
    # Calculate Z-Scores
    z_price = zscore(potential_df["GiaTrungBinh"])
    z_density = zscore(potential_df["MatDoChungCu"])
    z_hosp_cnt = zscore(potential_df["hospital_cnt"])
    z_mall_cnt = zscore(potential_df["mall_cnt"])
    z_metro_cnt = zscore(potential_df["metro_cnt"])
    z_univ_cnt = zscore(potential_df["university_cnt"])
    z_hosp_dist = zscore(potential_df["dist_hospital_m"])
    z_mall_dist = zscore(potential_df["dist_mall_m"])
    z_metro_dist = zscore(potential_df["dist_metro_m"])
    z_univ_dist = zscore(potential_df["dist_university_m"])
    
    # Potential score calculation from the R script weights
    potential_df["PotentialScore"] = (
        0.22 * z_price +
        0.18 * z_density +
        0.12 * z_hosp_cnt +
        0.12 * z_mall_cnt +
        0.14 * z_metro_cnt +
        0.12 * z_univ_cnt -
        0.04 * z_hosp_dist -
        0.02 * z_mall_dist -
        0.03 * z_metro_dist -
        0.01 * z_univ_dist
    )
    
    # Sort and rank
    potential_df = potential_df.sort_values(by="PotentialScore", ascending=False).reset_index(drop=True)
    potential_df["rank"] = potential_df.index + 1
    
    return potential_df

def main():
    print("==================================================")
    print("Starting Data Mining Project Orchestrator (run_all.py)")
    print("==================================================")
    
    ROOT = Path(__file__).resolve().parent.parent
    WEBAPP_DIR = ROOT / "webapp"
    WEBAPP_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Run Preprocessing
    ap_df, ward_df, hosp_in, mall_in, metro_in, univ_in = preprocess_data()
    
    # 2. Compute PotentialScore
    print("\nComputing PotentialScore for wards...")
    potential_df = compute_potential_score(ward_df, ap_df)
    potential_df.to_csv(ROOT / "phan_tich_theo_phuong_6_quan" / "mo_ta_thu_duc_potential_python.csv", index=False, encoding="utf-8-sig")
    print("PotentialScore ranking computed and saved.")
    
    # 3. Run Apriori
    print("\nRunning Apriori algorithm...")
    apriori_frequent, apriori_rules = run_apriori_on_apartments(ap_df, min_support=0.15, min_confidence=0.6)
    
    # 4. Run Rough Set
    print("\nRunning Rough Set analysis...")
    rough_set_res = run_rough_set_analysis(ap_df)
    
    # 5. Run ID3 Decision Tree
    print("\nRunning ID3 Decision Tree...")
    dt_res = run_id3_decision_tree(ap_df)
    
    # 6. Run Naive Bayes Classification
    print("\nRunning Naive Bayes classification...")
    nb_res = run_naive_bayes_classification(ap_df)
    
    # 7. Run K-Means Clustering
    print("\nRunning K-Means Clustering on wards...")
    kmeans_res = run_kmeans_clustering(potential_df, k=3)
    
    # 8. Run Kohonen SOM
    print("\nRunning Kohonen SOM on wards...")
    som_res = run_kohonen_som(potential_df, grid_size=10, epochs=100)
    
    # 9. Consolidated JSON structure
    print("\nConsolidating all results into JSON format...")
    
    def clean_val(val):
        if pd.isna(val) or val is None:
            return 0.0
        try:
            fval = float(val)
            if np.isnan(fval) or np.isinf(fval):
                return 0.0
            return fval
        except (ValueError, TypeError):
            return 0.0
            
    # Parse POIs
    pois_data = {
        "hospitals": [{"name": r["name"], "lat": clean_val(r["lat"]), "lon": clean_val(r["lon"])} for _, r in hosp_in.iterrows()],
        "malls": [{"name": r["name"], "lat": clean_val(r["lat"]), "lon": clean_val(r["lon"])} for _, r in mall_in.iterrows()],
        "metros": [{"name": r["name"], "lat": clean_val(r["lat"]), "lon": clean_val(r["lon"])} for _, r in metro_in.iterrows()],
        "universities": [{"name": r["name"], "lat": clean_val(r["lat"]), "lon": clean_val(r["lon"])} for _, r in univ_in.iterrows()]
    }
    
    # Parse apartments
    apartments_data = []
    for _, r in ap_df.iterrows():
        apartments_data.append({
            "name": r["TenChungCu"],
            "price": clean_val(r["GiaTrenM2"]),
            "lat": clean_val(r["latitude"]),
            "lon": clean_val(r["longitude"]),
            "district": r["Quan_huyen_goc"],
            "ward": r["Phuong_xa"],
            "price_segment": r["price_segment"],
            "dist_hospital": clean_val(r["dist_hospital_m"]),
            "dist_mall": clean_val(r["dist_mall_m"]),
            "dist_metro": clean_val(r["dist_metro_m"]),
            "dist_university": clean_val(r["dist_university_m"]),
            "dist_hospital_discrete": r["dist_hospital_discrete"],
            "dist_mall_discrete": r["dist_mall_discrete"],
            "dist_metro_discrete": r["dist_metro_discrete"],
            "dist_university_discrete": r["dist_university_discrete"]
        })
        
    # Parse wards
    wards_data = []
    for _, r in potential_df.iterrows():
        wards_data.append({
            "ward": r["Phuong_xa"],
            "district": r["Quan_huyen_goc"],
            "area_km2": clean_val(r["Dien_tich_km2"]),
            "apartment_count": int(r["SoChungCu"]),
            "density": clean_val(r["MatDoChungCu"]),
            "avg_price": clean_val(r["GiaTrungBinh"]),
            "median_price": clean_val(r["GiaTrungVi"]),
            "min_price": clean_val(r["GiaMin"]),
            "max_price": clean_val(r["GiaMax"]),
            "hospital_count": int(r["hospital_cnt"]),
            "mall_count": int(r["mall_cnt"]),
            "metro_count": int(r["metro_cnt"]),
            "university_count": int(r["university_cnt"]),
            "avg_dist_hospital": clean_val(r["dist_hospital_m"]),
            "avg_dist_mall": clean_val(r["dist_mall_m"]),
            "avg_dist_metro": clean_val(r["dist_metro_m"]),
            "avg_dist_university": clean_val(r["dist_university_m"]),
            "potential_score": clean_val(r["PotentialScore"]),
            "rank": int(r["rank"])
        })
        
    # Final data dictionary
    data_dict = {
        "apartments": apartments_data,
        "wards": wards_data,
        "pois": pois_data,
        "apriori": {
            "frequent_itemsets": apriori_frequent,
            "rules": apriori_rules
        },
        "rough_set": rough_set_res,
        "decision_tree": dt_res,
        "naive_bayes": nb_res,
        "kmeans": kmeans_res,
        "som": som_res
    }
    
    # Save to webapp/data.json
    output_json_path = WEBAPP_DIR / "data.json"
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=2, ensure_ascii=False)
        
    print(f"Data consolidation successful. Output saved to {output_json_path}")
    
    # Save combined GeoJSON to webapp/thu_duc_wards.geojson
    ward_geojson_path = WEBAPP_DIR / "thu_duc_wards.geojson"
    ward_df.to_file(ward_geojson_path, driver="GeoJSON")
    print(f"GeoJSON boundaries saved to {ward_geojson_path}")
    
    print("==================================================")
    print("ALL DATA MINING PROCESSES COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    main()
