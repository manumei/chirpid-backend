import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
from sklearn.model_selection import GroupShuffleSplit
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold

def try_split_with_seed(df, test_size, seed, min_test_segments, target_test_segments):
    """
    Try a single split with a given seed and evaluate its quality.
    
    Parameters:
    - df: DataFrame with 'class_id', 'author', and 'usable_segments' columns
    - test_size: Target test set size (0.0 to 1.0)
    - seed: Random seed for the split
    - min_test_segments: Minimum total segments per class in test set
    - target_test_segments: Target segments per class for test set
    - total_segments_per_class: Total segments per class in the dataset
    
    Returns:
    - (dev_df, test_df, score) if split is valid, None otherwise
    """
    try:
        gss = GroupShuffleSplit(
            n_splits=1, 
            test_size=test_size,
            random_state=seed
        )

        dev_indices, test_indices = next(gss.split(
            X=df, 
            y=df['class_id'], 
            groups=df['author']
        ))

        dev_df = df.iloc[dev_indices]
        test_df = df.iloc[test_indices]
        
        # Check if all classes are in both sets
        dev_classes = set(dev_df['class_id'])
        test_classes = set(test_df['class_id'])
        all_classes = set(df['class_id'])
        
        if not (all_classes <= dev_classes and all_classes <= test_classes):
            return None  # Skip if missing classes in either set
        
        # Check that each class in dev has at least 2 authors
        dev_authors_per_class = dev_df.groupby('class_id')['author'].nunique()
        if dev_authors_per_class.min() < 2:
            return None  # Skip if any class has fewer than 2 authors in dev
        
        # Check minimum test segments per class
        test_segments_per_class = test_df.groupby('class_id')['usable_segments'].sum()
        if test_segments_per_class.min() < min_test_segments:
            return None  # Skip if any class has too few test segments
        
        # Calculate stratification score based on segments (lower is better)
        actual_test_segments = test_df.groupby('class_id')['usable_segments'].sum().sort_index()
        
        # Mean absolute percentage error from target
        score = np.mean(np.abs(actual_test_segments.values - target_test_segments.values) / target_test_segments.values)
        
        return dev_df.copy(), test_df.copy(), score
    
    except Exception as e:
        raise ValueError(f"Error during split with seed {seed}: {e}") from e
        return None

def search_best_group_seed(df, test_size, max_attempts, min_test_segments):
    """
    Search for the best stratified split while maintaining author grouping.
    Based on total usable segments per class rather than sample counts.
    
    Parameters:
    - df: DataFrame with 'class_id', 'author', and 'usable_segments' columns
    - test_size: Target test set size (0.0 to 1.0)
    - max_attempts: Maximum number of random seeds to try
    - min_test_segments: Minimum total segments per class in test set
    
    Returns:
    - best_dev_df, best_test_df: Best split found
    - best_score: Stratification quality score
    """
    
    # Calculate target distribution based on total segments per class
    total_segments_per_class = df.groupby('class_id')['usable_segments'].sum().sort_index()
    target_test_segments = (total_segments_per_class * test_size).round().astype(int)
    
    best_score = float('inf')
    best_dev_df = None
    best_test_df = None
    best_seed = None
    
    for seed in range(max_attempts):
        result = try_split_with_seed(df, test_size, seed, min_test_segments, target_test_segments)
        
        if result is not None:
            dev_df, test_df, score = result
            
            if score < best_score:
                best_score = score
                best_dev_df = dev_df
                best_test_df = test_df
                best_seed = seed
                
                print(f"New best split found! Seed: {seed}, Score: {score:.3f}")
    
    if best_dev_df is None:
        if min_test_segments < 8:
            raise ValueError("No valid split found with current constraints. Consider relaxing min_test_segments.")
        return search_best_group_seed(df, test_size, max_attempts, min_test_segments=8)
    
    print(f"\nBest split found:")
    print(f"Seed: {best_seed}")
    print(f"Stratification score: {best_score:.3f}")
    print(f"Author overlap: {set(best_dev_df['author']) & set(best_test_df['author'])}")

    print(f"Segments in dev set: {best_dev_df['usable_segments'].sum()}")
    print(f"Segments in test set: {best_test_df['usable_segments'].sum()}")
    print(f"Dev segment%: {best_dev_df['usable_segments'].sum() / df['usable_segments'].sum():.2%}")
    print(f"Test segment%: {best_test_df['usable_segments'].sum() / df['usable_segments'].sum():.2%}")

    # Print distribution comparison
    print("\nSegment distribution comparison:")
    actual_test_segments = best_test_df.groupby('class_id')['usable_segments'].sum().sort_index()
    dev_segments = best_dev_df.groupby('class_id')['usable_segments'].sum().sort_index()
    target_dev_segments = total_segments_per_class - target_test_segments
    
    comparison_df = pd.DataFrame({
        'Target_Test_Segments': target_test_segments,
        'Actual_Test_Segments': actual_test_segments,
        'Target_Dev_Segments': target_dev_segments,
        'Actual_Dev_Segments': dev_segments,
        'Total_Segments': total_segments_per_class
    })
    
    print(tabulate(comparison_df, headers=comparison_df.columns, tablefmt='grid'))
    
    return best_dev_df, best_test_df, best_score

def try_kfold_split_with_seed(df, n_splits, seed, min_val_segments, target_val_segments):
    """
    Try a single K-fold split with a given seed and evaluate its quality.
    
    Parameters:
    - df: DataFrame with 'class_id', 'author', and 'usable_segments' columns
    - n_splits: Number of folds for cross-validation
    - seed: Random seed for the split
    - min_val_segments: Minimum total segments per class in each validation fold
    - target_val_segments: Target segments per class for validation folds
    
    Returns:
    - (folds, avg_score) if split is valid, None otherwise
    """
    try:
        # Try StratifiedGroupKFold first (better for stratification)
        try:
            skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
            splits = list(skf.split(df, df['class_id'], df['author']))
        except:
            # Fall back to GroupKFold if StratifiedGroupKFold fails
            gkf = GroupKFold(n_splits=n_splits)
            # Shuffle the dataframe for randomness
            df_shuffled = df.sample(frac=1, random_state=seed).reset_index(drop=True)
            splits = list(gkf.split(df_shuffled, df_shuffled['class_id'], df_shuffled['author']))
        
        folds = []
        fold_scores = []
        
        for fold_idx, (train_indices, val_indices) in enumerate(splits):
            if 'df_shuffled' in locals():
                train_df = df_shuffled.iloc[train_indices]
                val_df = df_shuffled.iloc[val_indices]
            else:
                train_df = df.iloc[train_indices]
                val_df = df.iloc[val_indices]
                # Check if all classes are in training set (validation can have missing classes)
            train_classes = set(train_df['class_id'])
            val_classes = set(val_df['class_id'])
            all_classes = set(df['class_id'])
            
            if not (all_classes <= train_classes):
                return None  # Skip if missing classes in training set
                # Check minimum validation segments per class (only for classes present in validation)
            val_segments_per_class = val_df.groupby('class_id')['usable_segments'].sum()
            if len(val_segments_per_class) > 0 and val_segments_per_class.min() < min_val_segments:
                return None  # Skip if any present class has too few validation segments
                # Calculate stratification score for this fold (only for classes present in validation)
            actual_val_segments = val_df.groupby('class_id')['usable_segments'].sum().sort_index()
            
            # Only compare classes that are actually present in validation set
            if len(actual_val_segments) > 0:
                target_val_segments_present = target_val_segments.loc[actual_val_segments.index]
                fold_score = np.mean(np.abs(actual_val_segments.values - target_val_segments_present.values) / 
                                    np.maximum(target_val_segments_present.values, 1))  # Avoid division by zero
            else:
                fold_score = 0  # No classes in validation set
            
            folds.append((train_df.copy(), val_df.copy()))
            fold_scores.append(fold_score)
        
        # Average score across all folds
        avg_score = np.mean(fold_scores)
        
        return folds, avg_score
    
    except Exception as e:
        return None

def search_best_group_seed_kfold(df, max_attempts, min_val_segments, n_splits):
    """
    Search for the best stratified K-fold split while maintaining author grouping.
    Based on total usable segments per class.
    
    Parameters:
    - df: DataFrame with 'class_id', 'author', and 'usable_segments' columns
    - n_splits: Number of folds for cross-validation
    - max_attempts: Maximum number of random seeds to try
    - min_val_segments: Minimum total segments per class in each validation fold
    
    Returns:
    - best_folds: List of (train_df, val_df) tuples for each fold
    - best_score: Average stratification quality score across all folds
    - best_seed: Random seed that produced the best split
    """
    
    # Calculate target distribution for validation (1/n_splits of total)
    total_segments_per_class = df.groupby('class_id')['usable_segments'].sum().sort_index()
    target_val_segments = (total_segments_per_class / n_splits).round().astype(int)
    
    print(f"Searching for best stratified {n_splits}-fold split across {max_attempts} attempts...")
    print(f"Target validation segments per class per fold: {target_val_segments.to_dict()}")
    
    best_score = float('inf')
    best_folds = None
    best_seed = None
    
    for seed in range(max_attempts):
        if seed % 5000 == 0:
            print(f"Attempt {seed}/{max_attempts - 1}...")
        result = try_kfold_split_with_seed(df, n_splits, seed, min_val_segments, target_val_segments)
        
        if result is not None:
            folds, avg_score = result
            
            if avg_score < best_score:
                best_score = avg_score
                best_folds = folds
                best_seed = seed
                print(f"New best {n_splits}-fold split found! Seed: {seed}, Avg Score: {avg_score:.3f}")
    
    if best_folds is None:
        if min_val_segments <= 4:
            raise ValueError("No valid split found with current constraints. Consider relaxing min_val_segments.")
        print("Warning: No valid split found with current constraints. Relaxing min_val_segments...")
        return search_best_group_seed_kfold(df, max_attempts, min_val_segments=5, n_splits=n_splits)
    
    print(f"\nBest {n_splits}-fold split found:")
    print(f"Seed: {best_seed}")
    print(f"Average stratification score: {best_score:.3f}")
    
    # Print fold statistics
    print(f"\nFold statistics:")
    for i, (train_df, val_df) in enumerate(best_folds):
        train_segments = train_df['usable_segments'].sum()
        val_segments = val_df['usable_segments'].sum()
        print(f"Fold {i+1}: Train={train_segments} segments, Val={val_segments} segments")
        
        # Check for author overlap (should be empty)
        author_overlap = set(train_df['author']) & set(val_df['author'])
        if author_overlap:
            print(f"WARNING: Author overlap in fold {i+1}: {author_overlap}")

    if n_splits == 4 and best_folds is not None:
        plot_fold_splits(best_folds)

    return best_folds, best_score, best_seed

def plot_fold_splits(folds):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for fold_idx, (train_df, val_df) in enumerate(folds):
        ax = axes[fold_idx // 2, fold_idx % 2]
        train_counts = train_df['class_id'].value_counts().sort_index()
        val_counts = val_df['class_id'].value_counts().sort_index()
        all_classes = sorted(set(train_counts.index) | set(val_counts.index))
        train_y = [train_counts.get(cls, 0) for cls in all_classes]
        val_y = [val_counts.get(cls, 0) for cls in all_classes]
        ax.plot(all_classes, train_y, label="Train", color="tab:blue")
        ax.plot(all_classes, val_y, label="Val", color="tab:orange")
        ax.set_title(f"Fold {fold_idx+1}")
        ax.set_xlabel("class_id")
        ax.set_ylabel("Num samples")
        ax.legend()
        ax.grid(True)
    plt.tight_layout()
    plt.show()