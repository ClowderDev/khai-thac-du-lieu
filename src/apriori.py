import pandas as pd
from collections import defaultdict
from itertools import combinations

def get_frequent_1_itemsets(transactions, min_sup_count):
    counts = defaultdict(int)
    for transaction in transactions:
        for item in transaction:
            counts[frozenset([item])] += 1
    return {itemset: count for itemset, count in counts.items() if count >= min_sup_count}

def generate_candidates(frequent_itemsets, k):
    candidates = set()
    list_frequent = list(frequent_itemsets.keys())
    n = len(list_frequent)
    for i in range(n):
        for j in range(i + 1, n):
            # Join step
            itemset1 = list_frequent[i]
            itemset2 = list_frequent[j]
            union = itemset1.union(itemset2)
            if len(union) == k:
                # Prune step
                is_valid = True
                for sub in combinations(union, k - 1):
                    if frozenset(sub) not in frequent_itemsets:
                        is_valid = False
                        break
                if is_valid:
                    candidates.add(union)
    return candidates

def get_frequent_k_itemsets(transactions, candidates, min_sup_count):
    counts = defaultdict(int)
    for transaction in transactions:
        t_set = set(transaction)
        for candidate in candidates:
            if candidate.issubset(t_set):
                counts[candidate] += 1
    return {itemset: count for itemset, count in counts.items() if count >= min_sup_count}

def apriori(transactions, min_support):
    n_transactions = len(transactions)
    min_sup_count = min_support * n_transactions
    
    # L1
    frequent_itemsets = {}
    L1 = get_frequent_1_itemsets(transactions, min_sup_count)
    frequent_itemsets.update(L1)
    
    L = L1
    k = 2
    while L:
        candidates = generate_candidates(L, k)
        if not candidates:
            break
        L_k = get_frequent_k_itemsets(transactions, candidates, min_sup_count)
        if not L_k:
            break
        frequent_itemsets.update(L_k)
        L = L_k
        k += 1
        
    return frequent_itemsets

def generate_association_rules(frequent_itemsets, min_confidence, n_transactions):
    rules = []
    for itemset, sup_count in frequent_itemsets.items():
        if len(itemset) < 2:
            continue
        # Generate all non-empty proper subsets of itemset
        for r in range(1, len(itemset)):
            for antecedent_tuple in combinations(itemset, r):
                antecedent = frozenset(antecedent_tuple)
                consequent = itemset.difference(antecedent)
                
                antecedent_sup = frequent_itemsets.get(antecedent)
                if antecedent_sup is None:
                    continue
                
                confidence = sup_count / antecedent_sup
                if confidence >= min_confidence:
                    support = sup_count / n_transactions
                    rules.append({
                        "antecedent": list(antecedent),
                        "consequent": list(consequent),
                        "support": float(support),
                        "confidence": float(confidence)
                    })
    return rules

def run_apriori_on_apartments(df, min_support=0.15, min_confidence=0.6):
    # Convert apartment dataframe into transaction list
    transactions = []
    for idx, row in df.iterrows():
        t = []
        # District
        t.append(row["district_discrete"])
        # POIs near
        if row["dist_hospital_discrete"] == "Gần":
            t.append("GầnBệnhViện")
        else:
            t.append("XaBệnhViện")
            
        if row["dist_mall_discrete"] == "Gần":
            t.append("GầnTTTM")
        else:
            t.append("XaTTTM")
            
        if row["dist_metro_discrete"] == "Gần":
            t.append("GầnMetro")
        else:
            t.append("XaMetro")
            
        if row["dist_university_discrete"] == "Gần":
            t.append("GầnĐạiHọc")
        else:
            t.append("XaĐạiHọc")
            
        # Price segment
        t.append("Giá" + row["price_segment"])
        transactions.append(t)
        
    frequent_itemsets = apriori(transactions, min_support)
    n_transactions = len(transactions)
    rules = generate_association_rules(frequent_itemsets, min_confidence, n_transactions)
    
    # Format frequent itemsets for export
    formatted_itemsets = []
    for itemset, count in frequent_itemsets.items():
        formatted_itemsets.append({
            "itemset": list(itemset),
            "support": float(count / n_transactions),
            "count": int(count)
        })
        
    # Sort rules by confidence and support
    rules = sorted(rules, key=lambda x: (x["confidence"], x["support"]), reverse=True)
    formatted_itemsets = sorted(formatted_itemsets, key=lambda x: x["support"], reverse=True)
    
    return formatted_itemsets, rules

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    from pathlib import Path
    
    ROOT = Path(__file__).resolve().parent.parent
    df = pd.read_csv(ROOT / "phan_tich_theo_phuong_6_quan" / "mo_ta_thu_duc_model_input_python.csv")
    frequent, rules = run_apriori_on_apartments(df, 0.15, 0.6)
    
    print(f"Apriori run completed.")
    print(f"Found {len(frequent)} frequent itemsets and {len(rules)} rules.")
    print("\nTop 5 association rules:")
    for rule in rules[:5]:
        print(f"{set(rule['antecedent'])} -> {set(rule['consequent'])} (Conf: {rule['confidence']:.2f}, Sup: {rule['support']:.2f})")
