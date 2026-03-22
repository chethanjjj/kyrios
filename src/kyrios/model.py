"""
model.py - Train and evaluate the XGBoost podium prediction model.
"""

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import LabelEncoder


FEATURES = ["GridPosition", "GapToPole", "InQ3", "Circuit", "Year",
            "ChampPoints", "ChampPosition", "ChampWins"]
TARGET = "Podium"


def prepare(df: pd.DataFrame):
    """
    Encode categoricals and return X, y, and groups (one group per race).

    Groups are used for splitting — we never want laps from the same race
    in both train and test.
    """
    df = df.copy()

    le = LabelEncoder()
    df["Circuit"] = le.fit_transform(df["Circuit"].astype(str))

    # Fill missing standings (round 1 has no prior standings)
    df[["ChampPoints", "ChampPosition", "ChampWins"]] = (
        df[["ChampPoints", "ChampPosition", "ChampWins"]].fillna(0)
    )

    X = df[FEATURES]
    y = df[TARGET]
    groups = df["Year"].astype(str) + "_" + df["Circuit"].astype(str)

    return X, y, groups


def train(df: pd.DataFrame):
    """
    Train an XGBoost classifier on the full dataset.

    Returns the fitted model.
    """
    X, y, _ = prepare(df)

    model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=(y == 0).sum() / (y == 1).sum(),  # handle class imbalance
        eval_metric="auc",
        random_state=42,
    )
    model.fit(X, y)
    return model


def evaluate(df: pd.DataFrame, n_splits: int = 5):
    """
    Evaluate model performance using group-based cross-validation.
    Each split keeps all drivers from a race together (no leakage).

    Returns a dict with mean AUC and a per-fold breakdown.
    """
    X, y, groups = prepare(df)

    splitter = GroupShuffleSplit(n_splits=n_splits, test_size=0.2, random_state=42)
    aucs = []

    for train_idx, test_idx in splitter.split(X, y, groups):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
            eval_metric="auc",
            random_state=42,
        )
        model.fit(X_train, y_train)

        y_prob = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_prob)
        aucs.append(auc)

    return {"mean_auc": np.mean(aucs), "fold_aucs": aucs}


def feature_importance(model, df: pd.DataFrame) -> pd.DataFrame:
    """
    Return feature importances as a sorted DataFrame.
    """
    X, _, _ = prepare(df)
    return (
        pd.DataFrame({"feature": X.columns, "importance": model.feature_importances_})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
