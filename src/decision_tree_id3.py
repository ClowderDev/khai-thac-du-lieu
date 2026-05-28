import sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import pandas as pd
import json
from pathlib import Path

class ID3Node:
    def __init__(self, attribute=None, value=None, is_leaf=False, decision=None):
        self.attribute = attribute  # Attribute to split on (if internal node)
        self.value = value          # The branch value (e.g. "Gần" or "Xa") that led to this node
        self.is_leaf = is_leaf      # True if leaf node
        self.decision = decision    # Price class if leaf node
        self.children = {}          # Dict mapping attribute value -> ID3Node child

def entropy(y):
    if len(y) == 0:
        return 0
    counts = y.value_counts()
    probs = counts / len(y)
    return -sum(probs * np.log2(probs + 1e-9))

def information_gain(df, attr, target_col):
    total_entropy = entropy(df[target_col])
    values = df[attr].unique()
    weighted_entropy = 0
    for val in values:
        subset = df[df[attr] == val]
        weighted_entropy += (len(subset) / len(df)) * entropy(subset[target_col])
    return total_entropy - weighted_entropy

def build_tree(df, attributes, target_col, default_decision, branch_val=None):
    # If dataset empty, return leaf with default decision
    if df.empty:
        return ID3Node(is_leaf=True, decision=default_decision, value=branch_val)
        
    # If all samples have same decision value, return leaf
    unique_decisions = df[target_col].unique()
    if len(unique_decisions) == 1:
        return ID3Node(is_leaf=True, decision=unique_decisions[0], value=branch_val)
        
    # Majority class in current subset
    majority_class = df[target_col].value_counts().idxmax()
    
    # If no attributes left, return majority class leaf
    if not attributes:
        return ID3Node(is_leaf=True, decision=majority_class, value=branch_val)
        
    # Choose best attribute to split on
    gains = {attr: information_gain(df, attr, target_col) for attr in attributes}
    best_attr = max(gains, key=gains.get)
    
    # If gain is very close to 0, stop split
    if gains[best_attr] < 1e-5:
        return ID3Node(is_leaf=True, decision=majority_class, value=branch_val)
        
    node = ID3Node(attribute=best_attr, value=branch_val)
    
    # Branching
    remaining_attributes = [a for a in attributes if a != best_attr]
    possible_values = df[best_attr].unique()
    
    for val in possible_values:
        subset = df[df[best_attr] == val]
        child = build_tree(subset, remaining_attributes, target_col, majority_class, branch_val=val)
        node.children[str(val)] = child
        
    return node

def predict_sample(node, sample):
    if node.is_leaf:
        return node.decision
    val = sample.get(node.attribute)
    if val is None or str(val) not in node.children:
        # Fallback to majority child decision
        if node.children:
            # Pick first available child to check, or return leaf approximation
            first_child = next(iter(node.children.values()))
            return predict_sample(first_child, sample)
        return "Trung bình" # default fallback
    return predict_sample(node.children[str(val)], sample)

def tree_to_dict(node):
    # Convert node to dict format for easy export to JSON for UI rendering
    if node.is_leaf:
        return {
            "is_leaf": True,
            "decision": node.decision,
            "value": node.value
        }
    else:
        return {
            "is_leaf": False,
            "attribute": node.attribute,
            "value": node.value,
            "children": {val: tree_to_dict(child) for val, child in node.children.items()}
        }

def print_tree(node, indent=""):
    if node.is_leaf:
        print(f"{indent}Leaf: Decision = {node.decision}")
    else:
        print(f"{indent}Split on attribute: {node.attribute}")
        for val, child in node.children.items():
            print(f"{indent}  Branch [{val}]:")
            print_tree(child, indent + "    ")

def run_id3_decision_tree(df):
    cond_attrs = [
        "dist_hospital_discrete",
        "dist_mall_discrete",
        "dist_metro_discrete",
        "dist_university_discrete",
        "district_discrete"
    ]
    target_col = "price_segment"
    
    default_decision = df[target_col].value_counts().idxmax()
    
    # Train test split (75/25) for evaluation
    np.random.seed(42)
    msk = np.random.rand(len(df)) < 0.75
    train_df = df[msk].reset_index(drop=True)
    test_df = df[~msk].reset_index(drop=True)
    
    # Train on full dataset for the visual tree
    full_tree = build_tree(df, cond_attrs, target_col, default_decision)
    
    # Train on train set for evaluation
    eval_tree = build_tree(train_df, cond_attrs, target_col, default_decision)
    
    # Evaluate
    train_preds = train_df.apply(lambda row: predict_sample(eval_tree, row), axis=1)
    test_preds = test_df.apply(lambda row: predict_sample(eval_tree, row), axis=1)
    
    train_acc = (train_preds == train_df[target_col]).mean()
    test_acc = (test_preds == test_df[target_col]).mean()
    
    tree_json_structure = tree_to_dict(full_tree)
    
    results = {
        "train_accuracy": float(train_acc),
        "test_accuracy": float(test_acc),
        "tree_dict": tree_json_structure
    }
    return results

if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    df = pd.read_csv(ROOT / "phan_tich_theo_phuong_6_quan" / "mo_ta_thu_duc_model_input_python.csv")
    results = run_id3_decision_tree(df)
    
    print("ID3 Decision Tree completed.")
    print(f"Train Accuracy: {results['train_accuracy']:.2f}")
    print(f"Test Accuracy: {results['test_accuracy']:.2f}")
    
    # Print sample dict representation
    # print(json.dumps(results['tree_dict'], indent=2, ensure_ascii=False)[:500])
