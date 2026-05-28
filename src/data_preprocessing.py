import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path

def preprocess_data():
    # Root is the project root (parent of this src/ folder)
    ROOT = Path(__file__).resolve().parent.parent
    DATASET_DIR = ROOT / "Dataset"
    OUTPUT_DIR = ROOT / "phan_tich_theo_phuong_6_quan"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    APARTMENT_CSV = DATASET_DIR / "hcm_apartment.csv"
    HOSPITAL_CSV = DATASET_DIR / "hospital.csv"
    MALL_CSV = DATASET_DIR / "mall.csv"
    METRO_CSV = DATASET_DIR / "metro.csv"
    UNIVERSITY_CSV = DATASET_DIR / "university.csv"

    WARD_GEOJSONS = [
        DATASET_DIR / "Quận 2.geojson",
        DATASET_DIR / "Quận 9.geojson",
        DATASET_DIR / "Thủ Đức.geojson"
    ]

    print("Step 1: Reading and merging ward GeoJSON boundaries...")
    ward_frames = []
    for geo_path in WARD_GEOJSONS:
        if not geo_path.exists():
            print(f"Error: GeoJSON file {geo_path} not found")
            return
        g = gpd.read_file(geo_path).to_crs("EPSG:4326")
        g["Quan_huyen_goc"] = g["Quan_huyen"]
        ward_frames.append(g[["Quan_huyen", "Phuong_xa", "geometry", "Quan_huyen_goc"]].copy())

    gdf_ward = gpd.GeoDataFrame(pd.concat(ward_frames, ignore_index=True), geometry="geometry", crs="EPSG:4326")
    gdf_ward["Quan_huyen"] = "Thành phố Thủ Đức"
    gdf_ward["Phuong_xa"] = gdf_ward["Phuong_xa"].astype(str).str.strip()

    # Calculate area in km2
    gdf_ward_metric = gdf_ward.to_crs(32648)
    gdf_ward["Dien_tich_km2"] = gdf_ward_metric.geometry.area / 1_000_000
    thu_duc_union = gdf_ward.geometry.unary_union

    print(f"Total wards loaded: {len(gdf_ward)}")

    print("Step 2: Reading and cleaning apartment data...")
    raw_ap = pd.read_csv(APARTMENT_CSV)
    df_ap = raw_ap.rename(columns={"Tên chung cư": "TenChungCu", "Giá trung bình trên m2": "GiaTrenM2"}).copy()
    df_ap = df_ap[["TenChungCu", "GiaTrenM2", "District", "Ward", "latitude", "longitude"]]
    df_ap["GiaTrenM2"] = pd.to_numeric(df_ap["GiaTrenM2"], errors="coerce")
    df_ap["latitude"] = pd.to_numeric(df_ap["latitude"], errors="coerce")
    df_ap["longitude"] = pd.to_numeric(df_ap["longitude"], errors="coerce")
    df_ap["District"] = df_ap["District"].astype(str).str.strip()
    df_ap["Ward"] = df_ap["Ward"].astype(str).str.strip()
    df_ap = df_ap.dropna(subset=["GiaTrenM2", "latitude", "longitude"]).reset_index(drop=True)

    gdf_ap = gpd.GeoDataFrame(df_ap, geometry=gpd.points_from_xy(df_ap["longitude"], df_ap["latitude"]), crs="EPSG:4326")

    print(f"Total apartments loaded: {len(gdf_ap)}")

    print("Step 3: Performing spatial join (apartments -> wards)...")
    gdf_join = gpd.sjoin(gdf_ap, gdf_ward[["Quan_huyen_goc", "Phuong_xa", "geometry"]], how="inner", predicate="within")
    gdf_join["Quan_huyen"] = "Thành phố Thủ Đức"
    gdf_join = gdf_join.drop(columns=["index_right"], errors="ignore")
    print(f"Apartments inside Thủ Đức region after spatial join: {len(gdf_join)}")

    print("Step 4: Reading and filtering POIs...")
    def read_poi(path, label):
        df = pd.read_csv(path)
        df = df[["name", "lat", "lon"]].copy()
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
        df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)
        g = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")
        g["poi_type"] = label
        return g

    def filter_in_thu_duc(gdf_poi):
        mask = gdf_poi.geometry.within(thu_duc_union) | gdf_poi.geometry.touches(thu_duc_union)
        return gdf_poi.loc[mask].copy()

    hospital_in = filter_in_thu_duc(read_poi(HOSPITAL_CSV, "hospital"))
    mall_in = filter_in_thu_duc(read_poi(MALL_CSV, "mall"))
    metro_in = filter_in_thu_duc(read_poi(METRO_CSV, "metro"))
    university_in = filter_in_thu_duc(read_poi(UNIVERSITY_CSV, "university"))

    print(f"POIs in Thủ Đức - Hospital: {len(hospital_in)}, Mall: {len(mall_in)}, Metro: {len(metro_in)}, University: {len(university_in)}")

    print("Step 5: Counting POIs per ward...")
    def count_poi_per_ward(poi_gdf, count_col):
        if poi_gdf.empty:
            return pd.DataFrame(columns=["Quan_huyen_goc", "Phuong_xa", count_col])
        j = gpd.sjoin(poi_gdf, gdf_ward[["Quan_huyen_goc", "Phuong_xa", "geometry"]], how="inner", predicate="within")
        return j.groupby(["Quan_huyen_goc", "Phuong_xa"]).size().reset_index(name=count_col)

    cnt_hospital = count_poi_per_ward(hospital_in, "hospital_cnt")
    cnt_mall = count_poi_per_ward(mall_in, "mall_cnt")
    cnt_metro = count_poi_per_ward(metro_in, "metro_cnt")
    cnt_university = count_poi_per_ward(university_in, "university_cnt")

    print("Step 6: Calculating ward statistics...")
    agg_stats = gdf_join.groupby(["Quan_huyen_goc", "Phuong_xa"])["GiaTrenM2"].agg(
        SoChungCu="count",
        GiaTrungBinh="mean",
        GiaTrungVi="median",
        GiaMin="min",
        GiaMax="max"
    ).reset_index()

    ward_enriched = gdf_ward[["Quan_huyen", "Quan_huyen_goc", "Phuong_xa", "Dien_tich_km2", "geometry"]].merge(
        agg_stats, on=["Quan_huyen_goc", "Phuong_xa"], how="left"
    )
    ward_enriched["SoChungCu"] = ward_enriched["SoChungCu"].fillna(0).astype(int)
    ward_enriched["MatDoChungCu"] = ward_enriched["SoChungCu"] / ward_enriched["Dien_tich_km2"]

    for df_cnt, col in zip([cnt_hospital, cnt_mall, cnt_metro, cnt_university], ["hospital_cnt", "mall_cnt", "metro_cnt", "university_cnt"]):
        ward_enriched = ward_enriched.merge(df_cnt, on=["Quan_huyen_goc", "Phuong_xa"], how="left")
        ward_enriched[col] = ward_enriched[col].fillna(0).astype(int)

    # Save ward csv
    ward_export = ward_enriched.drop(columns="geometry").copy()
    ward_export.to_csv(OUTPUT_DIR / "mo_ta_thu_duc_theo_phuong.csv", index=False, encoding="utf-8-sig")

    print("Step 7: Calculating minimum distances from apartments to POIs...")
    gdf_join_metric = gdf_join.to_crs(32648).reset_index(drop=True)

    def min_distance_m(src_metric, tgt_wgs):
        if tgt_wgs.empty:
            return pd.Series(np.nan, index=src_metric.index)
        tgt_metric = tgt_wgs.to_crs(32648)
        tgt_geo = tgt_metric.geometry
        # use distance to all geometries in target and take min
        return src_metric.geometry.apply(lambda geom: float(tgt_geo.distance(geom).min()))

    gdf_join_metric["dist_hospital_m"] = min_distance_m(gdf_join_metric, hospital_in)
    gdf_join_metric["dist_mall_m"] = min_distance_m(gdf_join_metric, mall_in)
    gdf_join_metric["dist_metro_m"] = min_distance_m(gdf_join_metric, metro_in)
    gdf_join_metric["dist_university_m"] = min_distance_m(gdf_join_metric, university_in)

    print("Step 8: Merging everything and performing discretization...")
    apartment_enriched = gdf_join_metric.drop(columns="geometry").merge(
        ward_enriched[["Quan_huyen_goc", "Phuong_xa", "Dien_tich_km2", "SoChungCu", "MatDoChungCu", "hospital_cnt", "mall_cnt", "metro_cnt", "university_cnt"]],
        on=["Quan_huyen_goc", "Phuong_xa"],
        how="left"
    )

    # Discretization function
    def bin_price(p):
        if p < 50:
            return "Thấp"
        elif p < 80:
            return "Trung bình"
        elif p < 150:
            return "Cao"
        else:
            return "Rất cao"

    def bin_dist(d):
        return "Gần" if d < 1500 else "Xa"

    apartment_enriched["price_segment"] = apartment_enriched["GiaTrenM2"].apply(bin_price)
    apartment_enriched["dist_hospital_discrete"] = apartment_enriched["dist_hospital_m"].apply(bin_dist)
    apartment_enriched["dist_mall_discrete"] = apartment_enriched["dist_mall_m"].apply(bin_dist)
    apartment_enriched["dist_metro_discrete"] = apartment_enriched["dist_metro_m"].apply(bin_dist)
    apartment_enriched["dist_university_discrete"] = apartment_enriched["dist_university_m"].apply(bin_dist)
    apartment_enriched["district_discrete"] = apartment_enriched["Quan_huyen_goc"]

    # Fill NaN values in distances
    dist_cols = ["dist_hospital_m", "dist_mall_m", "dist_metro_m", "dist_university_m"]
    for col in dist_cols:
        apartment_enriched[col] = apartment_enriched[col].fillna(apartment_enriched[col].median())

    # Export CSVs
    apartment_enriched.to_csv(OUTPUT_DIR / "mo_ta_thu_duc_model_input_python.csv", index=False, encoding="utf-8-sig")
    print("Preprocessed apartment dataset saved successfully.")

    # Return data structures for downstream processing
    return apartment_enriched, ward_enriched, hospital_in, mall_in, metro_in, university_in

if __name__ == "__main__":
    preprocess_data()

