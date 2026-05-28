import sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import pandas as pd
from pathlib import Path

class NaiveBayesClassifier:
    def __init__(self, laplace=1.0):
        self.laplace = laplace
        self.classes = []
        self.priors = {}
        self.likelihoods = {} # dict of dicts: likelihoods[class_val][attr][attr_val] = prob
        self.vocab_sizes = {} # vocabulary size for each attribute for smoothing

    def fit(self, df, cond_attrs, target_col):
        n_samples = len(df)
        self.classes = df[target_col].unique()
        
        # Calculate vocabulary sizes for each attribute
        for attr in cond_attrs:
            self.vocab_sizes[attr] = len(df[attr].unique())
            
        # 1. Priors
        class_counts = df[target_col].value_counts()
        for c in self.classes:
            self.priors[c] = class_counts.get(c, 0) / n_samples
            self.likelihoods[c] = {}
            
            # Sub-dataframe for class c
            df_c = df[df[target_col] == c]
            n_samples_c = len(df_c)
            
            # 2. Likelihoods
            for attr in cond_attrs:
                self.likelihoods[c][attr] = {}
                attr_counts = df_c[attr].value_counts()
                
                # We smooth over all possible values of this attribute present in the whole dataset
                all_values = df[attr].unique()
                vocab_size = self.vocab_sizes[attr]
                
                for val in all_values:
                    # Count with Laplace smoothing
                    count_val = attr_counts.get(val, 0)
                    prob = (count_val + self.laplace) / (n_samples_c + self.laplace * vocab_size)
                    self.likelihoods[c][attr][val] = prob

    def predict_sample(self, sample, cond_attrs):
        best_class = None
        max_posterior = -1.0
        
        for c in self.classes:
            # We compute class posterior proportional to prior * product(likelihoods)
            posterior = self.priors[c]
            for attr in cond_attrs:
                val = sample.get(attr)
                # If attribute value was not seen, fallback using smoothing formula
                prob = self.likelihoods[c][attr].get(val, self.laplace / (len(self.likelihoods[c][attr]) + self.vocab_sizes[attr] * self.laplace))
                posterior *= prob
                
            if posterior > max_posterior:
                max_posterior = posterior
                best_class = c
                
        return best_class

    def get_model_params(self):
        # Format the parameters for JSON export
        return {
            "classes": list(self.classes),
            "priors": {str(c): float(p) for c, p in self.priors.items()},
            "likelihoods": {
                str(c): {
                    str(attr): {str(val): float(prob) for val, prob in attr_dict.items()}
                    for attr, attr_dict in class_dict.items()
                }
                for c, class_dict in self.likelihoods.items()
            }
        }

def run_naive_bayes_classification(df):
    cond_attrs = [
        "dist_hospital_discrete",
        "dist_mall_discrete",
        "dist_metro_discrete",
        "dist_university_discrete",
        "district_discrete"
    ]
    target_col = "price_segment"
    
    np.random.seed(42)
    msk = np.random.rand(len(df)) < 0.75
    train_df = df[msk].reset_index(drop=True)
    test_df = df[~msk].reset_index(drop=True)
    
    # Train full model for parameters
    full_classifier = NaiveBayesClassifier()
    full_classifier.fit(df, cond_attrs, target_col)
    model_params = full_classifier.get_model_params()
    
    # Train evaluation model
    eval_classifier = NaiveBayesClassifier()
    eval_classifier.fit(train_df, cond_attrs, target_col)
    
    train_preds = train_df.apply(lambda row: eval_classifier.predict_sample(row, cond_attrs), axis=1)
    test_preds = test_df.apply(lambda row: eval_classifier.predict_sample(row, cond_attrs), axis=1)
    
    train_acc = (train_preds == train_df[target_col]).mean()
    test_acc = (test_preds == test_df[target_col]).mean()
    
    results = {
        "train_accuracy": float(train_acc),
        "test_accuracy": float(test_acc),
        "model_params": model_params
    }
    return results

if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    df = pd.read_csv(ROOT / "phan_tich_theo_phuong_6_quan" / "mo_ta_thu_duc_model_input_python.csv")
    results = run_naive_bayes_classification(df)
    
    print("Naive Bayes Classifier completed.")
    print(f"Train Accuracy: {results['train_accuracy']:.2f}")
    print(f"Test Accuracy: {results['test_accuracy']:.2f}")
