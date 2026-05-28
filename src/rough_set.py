import sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import pandas as pd
from itertools import combinations
from pathlib import Path

def get_indiscernibility_partition(df, attributes):
    # Groups objects by the values of the specified attributes
    groups = df.groupby(list(attributes)).groups
    return [set(indices) for indices in groups.values()]

def compute_approximations(df, partition, decision_attr, decision_val):
    # Target set of objects: where decision_attr == decision_val
    X = set(df[df[decision_attr] == decision_val].index)
    
    lower_approx = set()
    upper_approx = set()
    
    for eq_class in partition:
        if eq_class.issubset(X):
            lower_approx.update(eq_class)
        if not eq_class.isdisjoint(X):
            upper_approx.update(eq_class)
            
    boundary_region = upper_approx.difference(lower_approx)
    
    accuracy = len(lower_approx) / len(upper_approx) if len(upper_approx) > 0 else 1.0
    
    return lower_approx, upper_approx, boundary_region, accuracy

def compute_dependency(df, cond_attrs, decision_attr):
    # Dependency of decision attribute on conditional attributes:
    # gamma = sum(|lower_approx_i|) / |U| for all decision classes i
    U_size = len(df)
    decision_values = df[decision_attr].unique()
    cond_partition = get_indiscernibility_partition(df, cond_attrs)
    
    positive_region_size = 0
    for val in decision_values:
        lower_approx, _, _, _ = compute_approximations(df, cond_partition, decision_attr, val)
        positive_region_size += len(lower_approx)
        
    return positive_region_size / U_size

def find_reducts(df, cond_attrs, decision_attr):
    # Construct decision-relative discernibility matrix
    # for pairs (i, j) with df[decision_attr][i] != df[decision_attr][j]
    U_size = len(df)
    clauses = []
    
    for i in range(U_size):
        for j in range(i + 1, U_size):
            if df.loc[i, decision_attr] != df.loc[j, decision_attr]:
                # find differing conditional attributes
                diff_attrs = set()
                for attr in cond_attrs:
                    if df.loc[i, attr] != df.loc[j, attr]:
                        diff_attrs.add(attr)
                if diff_attrs:
                    clauses.append(diff_attrs)
                    
    # Find minimal hitting sets (reducts) of the clauses
    reducts = []
    # Search all subsets of cond_attrs in order of size
    for r in range(1, len(cond_attrs) + 1):
        for comb in combinations(cond_attrs, r):
            comb_set = set(comb)
            # check if it hits all clauses
            hits_all = True
            for clause in clauses:
                if not comb_set.intersection(clause):
                    hits_all = False
                    break
            if hits_all:
                # check if it is minimal (no subset of comb_set is already a reduct)
                is_minimal = True
                for existing_reduct in reducts:
                    if set(existing_reduct).issubset(comb_set):
                        is_minimal = False
                        break
                if is_minimal:
                    reducts.append(list(comb))
                    
    return reducts

def run_rough_set_analysis(df):
    cond_attrs = [
        "dist_hospital_discrete",
        "dist_mall_discrete",
        "dist_metro_discrete",
        "dist_university_discrete",
        "district_discrete"
    ]
    decision_attr = "price_segment"
    
    # 1. Compute Indiscernibility partitions for C
    c_partition = get_indiscernibility_partition(df, cond_attrs)
    
    # 2. Lower and Upper Approximations for each price segment
    decision_classes = df[decision_attr].unique()
    approximations = {}
    for d_val in decision_classes:
        lower, upper, boundary, acc = compute_approximations(df, c_partition, decision_attr, d_val)
        approximations[d_val] = {
            "lower_size": len(lower),
            "upper_size": len(upper),
            "boundary_size": len(boundary),
            "accuracy": float(acc),
            "lower_objects": [int(o) for o in list(lower)[:10]], # sample 10 objects
            "upper_objects": [int(o) for o in list(upper)[:10]]
        }
        
    # 3. Attribute Dependency gamma(C, D)
    gamma = compute_dependency(df, cond_attrs, decision_attr)
    
    # 4. Reducts
    reducts = find_reducts(df, cond_attrs, decision_attr)
    
    # Map raw attribute names to friendly names for UI representation
    friendly_names = {
        "dist_hospital_discrete": "Bệnh viện",
        "dist_mall_discrete": "TTTM",
        "dist_metro_discrete": "Ga Metro",
        "dist_university_discrete": "Đại học",
        "district_discrete": "Quận"
    }
    
    friendly_reducts = [[friendly_names[a] for a in r] for r in reducts]
    
    results = {
        "dependency_degree": float(gamma),
        "approximations": approximations,
        "reducts": reducts,
        "friendly_reducts": friendly_reducts,
        "attributes": cond_attrs
    }
    return results

if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    df = pd.read_csv(ROOT / "phan_tich_theo_phuong_6_quan" / "mo_ta_thu_duc_model_input_python.csv")
    results = run_rough_set_analysis(df)
    
    print("Rough Set Analysis completed.")
    print(f"Degree of dependency (gamma): {results['dependency_degree']:.3f}")
    print("Reducts found:")
    for r, fr in zip(results['reducts'], results['friendly_reducts']):
        print(f"  - {fr} (original keys: {r})")
        
    print("\nApproximations summary:")
    for d_val, app in results['approximations'].items():
        print(f"  Class {d_val}: Accuracy = {app['accuracy']:.3f}, Lower size = {app['lower_size']}, Upper size = {app['upper_size']}")
