import torch
import torch.nn as torch_nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import classification_report
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.model_selection import cross_val_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from collections import Counter
from sklearn.utils.class_weight import compute_class_weight, compute_sample_weight
import numpy as np
import requests
import optuna
import json
from pathlib import Path
from .helpers import getADX, getMACD, getMovingAvg, getRSI, getStochastic, add_extra_features
import os
import yfinance as yf
import pandas as pd
import requests as req_session
optuna.logging.set_verbosity(optuna.logging.WARNING)

PARAMS_FILE = "best_params.json"


# =========================
# PyTorch Model
# =========================
class TorchNet(torch_nn.Module):
    def __init__(self, input_dim, num_classes=3):
        super().__init__()
        self.net = torch_nn.Sequential(
            torch_nn.Linear(input_dim, 128),
            torch_nn.BatchNorm1d(128),
            torch_nn.ReLU(),
            torch_nn.Dropout(0.3),
            torch_nn.Linear(128, 64),
            torch_nn.BatchNorm1d(64),
            torch_nn.ReLU(),
            torch_nn.Dropout(0.2),
            torch_nn.Linear(64, 32),
            torch_nn.ReLU(),
            torch_nn.Linear(32, num_classes)
        )

    def forward(self, x):
        return self.net(x)


class TorchClassifierWrapper(BaseEstimator, ClassifierMixin):
    def __init__(self, input_dim, num_classes=3, epochs=50, batch_size=32, lr=0.001, class_weights=None):
        self.input_dim = input_dim
        self.num_classes = num_classes
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.class_weights = class_weights
        self.model = None
        self.classes_ = np.array([0, 1, 2])

    def fit(self, X, y):
        split = int(len(X) * 0.9)
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]

        X_tensor     = torch.tensor(X_train, dtype=torch.float32)
        y_tensor     = torch.tensor(y_train, dtype=torch.long)
        X_val_tensor = torch.tensor(X_val,   dtype=torch.float32)
        y_val_tensor = torch.tensor(y_val,   dtype=torch.long)

        loader    = DataLoader(TensorDataset(X_tensor, y_tensor), batch_size=self.batch_size, shuffle=True)
        self.model = TorchNet(self.input_dim, self.num_classes)
        optimizer  = optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=1e-4)
        scheduler  = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)

        if self.class_weights is not None:
            weights_tensor = torch.tensor(self.class_weights, dtype=torch.float32)
            criterion = torch_nn.CrossEntropyLoss(weight=weights_tensor)
        else:
            criterion = torch_nn.CrossEntropyLoss()

        best_val_loss    = float('inf')
        patience_counter = 0
        best_weights     = None

        for epoch in range(self.epochs):
            self.model.train()
            epoch_loss = 0
            for X_batch, y_batch in loader:
                optimizer.zero_grad()
                loss = criterion(self.model(X_batch), y_batch)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            avg_train_loss = epoch_loss / len(loader)
            self.model.eval()
            with torch.no_grad():
                val_logits = self.model(X_val_tensor)
                val_loss   = criterion(val_logits, y_val_tensor).item()
                val_preds  = torch.argmax(val_logits, dim=1).numpy()
                val_acc    = np.mean(val_preds == np.array(y_val))

            scheduler.step(val_loss)
            print(f"Epoch {epoch+1}/{self.epochs} | Train: {avg_train_loss:.4f} | Val: {val_loss:.4f} | Acc: {val_acc:.4f}")

            if val_loss < best_val_loss:
                best_val_loss    = val_loss
                best_weights     = {k: v.clone() for k, v in self.model.state_dict().items()}
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= 10:
                    print("Early stopping triggered")
                    self.model.load_state_dict(best_weights)
                    break

        return self

    def predict_proba(self, X):
        self.model.eval()
        X_tensor = torch.tensor(X, dtype=torch.float32)
        with torch.no_grad():
            return torch.softmax(self.model(X_tensor), dim=1).numpy()

    def predict(self, X):
        return np.argmax(self.predict_proba(X), axis=1)


# =========================
# Hyperparameter Tuning
# =========================
def tune_hyperparams(X_train, y_train):
    print("Tuning hyperparameters...")

    # ── Random Forest ─────────────────────────────────────────────
    def rf_objective(trial):
        params = {
            "n_estimators":    trial.suggest_int("n_estimators", 100, 1000),
            "max_depth":       trial.suggest_int("max_depth", 5, 30),
            "min_samples_leaf":trial.suggest_int("min_samples_leaf", 1, 20),
            "max_features":    trial.suggest_categorical("max_features", ["sqrt", "log2"]),
            "class_weight":    "balanced",
            "random_state":    42
        }
        model = RandomForestClassifier(**params)
        return cross_val_score(model, X_train, y_train, cv=3, scoring="accuracy").mean()

    rf_study = optuna.create_study(direction="maximize")
    rf_study.optimize(rf_objective, n_trials=30)
    best_rf = rf_study.best_params
    best_rf["class_weight"] = "balanced"
    best_rf["random_state"] = 42
    print(f"Best RF  params: {best_rf}  | acc: {rf_study.best_value:.4f}")

    # ── XGBoost ───────────────────────────────────────────────────
    def xgb_objective(trial):
        params = {
            "n_estimators":     trial.suggest_int("n_estimators", 100, 1000),
            "max_depth":        trial.suggest_int("max_depth", 3, 10),
            "learning_rate":    trial.suggest_float("learning_rate", 0.001, 0.3, log=True),
            "subsample":        trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "verbosity":        0
        }
        model = XGBClassifier(**params)
        return cross_val_score(model, X_train, y_train, cv=3, scoring="accuracy").mean()

    xgb_study = optuna.create_study(direction="maximize")
    xgb_study.optimize(xgb_objective, n_trials=30)
    best_xgb = xgb_study.best_params
    best_xgb["verbosity"] = 0
    print(f"Best XGB params: {best_xgb} | acc: {xgb_study.best_value:.4f}")

    # ── LightGBM ──────────────────────────────────────────────────
    def lgb_objective(trial):
        params = {
            "n_estimators":     trial.suggest_int("n_estimators", 100, 1000),
            "learning_rate":    trial.suggest_float("learning_rate", 0.001, 0.3, log=True),
            "max_depth":        trial.suggest_int("max_depth", 3, 15),
            "num_leaves":       trial.suggest_int("num_leaves", 20, 150),
            "min_child_samples":trial.suggest_int("min_child_samples", 5, 50),
            "class_weight":     "balanced",
            "verbose":          -1
        }
        model = LGBMClassifier(**params)
        return cross_val_score(model, X_train, y_train, cv=3, scoring="accuracy").mean()

    lgb_study = optuna.create_study(direction="maximize")
    lgb_study.optimize(lgb_objective, n_trials=30)
    best_lgb = lgb_study.best_params
    best_lgb["class_weight"] = "balanced"
    best_lgb["verbose"] = -1
    print(f"Best LGB params: {best_lgb} | acc: {lgb_study.best_value:.4f}")

    # save so we don't retune every call
    with open(PARAMS_FILE, "w") as f:
        json.dump({"rf": best_rf, "xgb": best_xgb, "lgb": best_lgb}, f, indent=2)
    print(f"Saved best params to {PARAMS_FILE}")

    return best_rf, best_xgb, best_lgb


def load_or_tune_params(X_train, y_train):
    if os.path.exists(PARAMS_FILE):
        print(f"Loading saved params from {PARAMS_FILE}")
        with open(PARAMS_FILE, "r") as f:
            params = json.load(f)
        return params["rf"], params["xgb"], params["lgb"]
    return tune_hyperparams(X_train, y_train)


# =========================
# Helpers
# =========================
required = [
    "moving5", "moving10", "moving20", "RSI", "GainLoss",
    "stochastic", "macd", "macdSignal", "macdHist", "adx", "Volume", "Close",
    "distance_from_52w_high", "distance_from_52w_low",
    "volume_ratio", "atr", "price_vs_ma50", "price_vs_ma200"
]


def extract_features(data, idx, row):
    return [
        # moving average ratios
        row["Close"] / row["moving5"],
        row["Close"] / row["moving10"],
        row["Close"] / row["moving20"],
        row["moving5"] / row["moving20"],
        # price momentum
        row["Close"] / data[idx-1]["Close"]  - 1,
        row["Close"] / data[idx-5]["Close"]  - 1,
        row["Close"] / data[idx-10]["Close"] - 1,
        row["Close"] / data[idx-20]["Close"] - 1,
        # technical indicators
        row["RSI"],
        row["GainLoss"],
        row["stochastic"],
        row["adx"],
        row["macd"]       / row["Close"],
        row["macdSignal"] / row["Close"],
        row["macdHist"]   / row["Close"],
        row["Volume"]     / row["moving5"],
        # new features
        row["distance_from_52w_high"],
        row["distance_from_52w_low"],
        row["volume_ratio"],
        min(row["atr"] / row["Close"], 0.2),  # normalized + capped at 20%
        row["price_vs_ma50"],
        row["price_vs_ma200"],
    ]


def fetch_stock(ticker: str):
    return get_stock_data(ticker)


def analyze(target: str, others: list[str]) -> dict:
    all_tickers = [target] + others
    stock_data  = {}

    # Fetch and index all stocks by date
    for ticker in all_tickers:
        data = fetch_stock(ticker)
        print(f"{ticker}: {len(data)} rows")

        if ticker == target:
            # calculate std on returns once outside the loop
            closes    = [row['Close'] for row in data]
            returns   = pd.Series(closes).pct_change().dropna()
            std       = returns.std()
            threshold = std * 0.5
            print(f"Using threshold: {threshold:.4f} ({threshold*100:.2f}%)")

            for i in range(len(data) - 5):
                y = (data[i+5]['Close'] - data[i]['Close']) / data[i]['Close']
                if y > threshold:
                    data[i]['future'] = "Buy"
                elif y < -threshold:
                    data[i]['future'] = "Sell"
                else:
                    data[i]['future'] = "Neutral"

        stock_data[ticker] = {row['Date']: (idx, row, data) for idx, row in enumerate(data)}

    # Build aligned feature rows
    all_features = []
    all_labels   = []

    for date, (t_idx, t_row, t_data) in stock_data[target].items():
        if t_idx < 252:  # need 252 days for 52w features
            continue
        if 'future' not in t_row:
            continue
        if not all(k in t_row for k in required):
            continue

        skip = False
        for ticker in others:
            if ticker not in stock_data or date not in stock_data[ticker]:
                skip = True
                break
            o_idx, o_row, o_data = stock_data[ticker][date]
            if o_idx < 252 or not all(k in o_row for k in required):
                skip = True
                break
        if skip:
            continue

        row_features = extract_features(t_data, t_idx, t_row)
        for ticker in others:
            o_idx, o_row, o_data = stock_data[ticker][date]
            row_features += extract_features(o_data, o_idx, o_row)

        all_features.append(row_features)
        all_labels.append(t_row['future'])

    print(f"Total aligned samples: {len(all_features)}")
    print(f"Labels: {Counter(all_labels)}")

    # Preprocessing
    label_map   = {"Sell": 0, "Neutral": 1, "Buy": 2}
    y_numeric   = np.array([label_map[l] for l in all_labels])
    split       = int(len(all_features) * 0.8)

    X_train_raw = np.array(all_features[:split])
    X_test_raw  = np.array(all_features[split:])
    y_train     = y_numeric[:split]
    y_test      = y_numeric[split:]

    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_test  = scaler.transform(X_test_raw)

    class_weights  = compute_class_weight('balanced', classes=np.array([0, 1, 2]), y=y_train)
    sample_weights = compute_sample_weight('balanced', y_train)

    # load saved params or tune if none exist
    best_rf, best_xgb, best_lgb = load_or_tune_params(X_train, y_train)

    # Train models
    rf  = RandomForestClassifier(**best_rf)
    rf.fit(X_train, y_train)

    xgb = XGBClassifier(**best_xgb)
    xgb.fit(X_train, y_train, sample_weight=sample_weights)

    lgb = LGBMClassifier(**best_lgb)
    lgb.fit(X_train, y_train)

    torch_model = TorchClassifierWrapper(
        input_dim=X_train.shape[1],
        epochs=200,
        batch_size=16,
        lr=0.001,
        class_weights=class_weights
    )
    torch_model.fit(X_train, y_train)

    ensemble = VotingClassifier(
        estimators=[('rf', rf), ('xgb', xgb), ('lgb', lgb), ('torch_nn', torch_model)],
        voting='soft'
    )
    ensemble.fit(X_train, y_train)

    preds    = ensemble.predict(X_test)
    accuracy = ensemble.score(X_test, y_test)
    report   = classification_report(y_test, preds, target_names=["Sell", "Neutral", "Buy"], output_dict=True)

    # Predict latest signal
    latest_features = np.array([all_features[-1]])
    latest_scaled   = scaler.transform(latest_features)
    latest_pred     = ensemble.predict(latest_scaled)[0]
    latest_proba    = ensemble.predict_proba(latest_scaled)[0]
    label_map_inv   = {0: "Sell", 1: "Neutral", 2: "Buy"}

    return {
        "target": target,
        "others": others,
        "accuracy": accuracy,
        "report": report,
        "prediction": label_map_inv[latest_pred],
        "probabilities": {
            "Sell":    float(latest_proba[0]),
            "Neutral": float(latest_proba[1]),
            "Buy":     float(latest_proba[2]),
        }
    }


# =========================
# Correlation functions
# =========================
def calculate_correlation(stock1: list, stock2: list) -> float:
    df1 = pd.DataFrame(stock1)
    df2 = pd.DataFrame(stock2)

    df1['Date'] = pd.to_datetime(df1['Date']).dt.date
    df2['Date'] = pd.to_datetime(df2['Date']).dt.date

    df1['return'] = df1['Close'].pct_change()
    df2['return'] = df2['Close'].pct_change()

    merged = pd.merge(
        df1[['Date', 'return']],
        df2[['Date', 'return']],
        on='Date',
        suffixes=('_1', '_2')
    )

    if merged.empty:
        return 0.0

    correlation = merged['return_1'].corr(merged['return_2'])
    return round(float(correlation), 4)


def calculate_lagged_correlation(stock1: list, stock2: list, lag: int) -> float:
    df1 = pd.DataFrame(stock1)
    df2 = pd.DataFrame(stock2)

    df1['Date'] = pd.to_datetime(df1['Date']).dt.date
    df2['Date'] = pd.to_datetime(df2['Date']).dt.date

    df1['return'] = df1['Close'].pct_change()
    df2['return'] = df2['Close'].pct_change()

    merged = pd.merge(
        df1[['Date', 'return']],
        df2[['Date', 'return']],
        on='Date',
        suffixes=('_1', '_2')
    )

    if merged.empty:
        return 0.0

    merged['return_2_lagged'] = merged['return_2'].shift(lag)
    correlation = merged['return_1'].corr(merged['return_2_lagged'])
    return round(float(correlation), 4)


def compare(ticker, ticker_list):
    stock   = get_stock_data(ticker)
    if not stock:
        return {"ticker": ticker, "correlations": {}}
    results = {}

    for i in ticker_list:
        print(i)
        comparison_stock = get_stock_data(i)
        regular = calculate_correlation(stock, comparison_stock)
        results[i] = {"regular": regular}

    return {
        "ticker": ticker,
        "correlations": results
    }


# =========================
# Data helpers
# =========================
def get_tickers():
    data_folder = Path(__file__).parent.parent.parent / "data"
    ls = []
    for file in data_folder.iterdir():
        ls.append(file.name.split(".")[0])
    return ls


def get_stock_data(ticker: str, start: str = "2010-01-01", end: str = "2025-01-01"):
    if not start:
        start = "2010-01-01"
    if not end:
        end = "2025-01-01"
    ticker = ticker.upper()
    os.makedirs("data", exist_ok=True)
    file_path = f"data/{ticker}.csv"
    session = req_session.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    if os.path.exists(file_path):
        print("data in file")
        data = pd.read_csv(file_path)
        data["Date"] = pd.to_datetime(data["Date"])
        data_start = data["Date"].min()
        data_end = data["Date"].max()

        if data_start > pd.to_datetime(start) or data_end < pd.to_datetime(end):
            print("file doesn't cover date range, re-downloading...")
            os.remove(file_path)  
            data = yf.download(ticker, start=start, end=end)

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)

            data = data.reset_index()
            data.to_csv(file_path, index=False)
            data["Date"] = pd.to_datetime(data["Date"])
    else:
        print("downloading data...")
        data = yf.download(ticker, start=start, end=end)

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)

        data = data.reset_index()
        data.to_csv(file_path, index=False)
        data["Date"] = pd.to_datetime(data["Date"])
    print(data)
    data["Date"] = pd.to_datetime(data["Date"])
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    data = data[(data["Date"] >= start) & (data["Date"] <= end)]
    data = data[(data["Date"] >= pd.to_datetime(start)) & (data["Date"] <= pd.to_datetime(end))]
    print(data)
    result = data.where(pd.notnull(data), None).to_dict(orient="records")
    getMovingAvg(result, 5)
    getMovingAvg(result, 10)
    getMovingAvg(result, 20)
    getRSI(result, 10)
    getStochastic(result)
    getMACD(result)
    add_extra_features(result)
    getADX(result)
    return result