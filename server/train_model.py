import torch
import torch.nn as torch_nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import classification_report
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator, ClassifierMixin

from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from collections import Counter
from sklearn.utils.class_weight import compute_class_weight, compute_sample_weight

import numpy as np
import requests


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


# =========================
# Sklearn Wrapper
# =========================
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

        X_tensor = torch.tensor(X_train, dtype=torch.float32)
        y_tensor = torch.tensor(y_train, dtype=torch.long)

        X_val_tensor = torch.tensor(X_val, dtype=torch.float32)
        y_val_tensor = torch.tensor(y_val, dtype=torch.long)

        loader = DataLoader(TensorDataset(X_tensor, y_tensor),
                            batch_size=self.batch_size, shuffle=True)

        self.model = TorchNet(self.input_dim, self.num_classes)

        optimizer = optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=1e-4)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)

        if self.class_weights is not None:
            weights_tensor = torch.tensor(self.class_weights, dtype=torch.float32)
            criterion = torch_nn.CrossEntropyLoss(weight=weights_tensor)
        else:
            criterion = torch_nn.CrossEntropyLoss()

        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0
        best_weights = None

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
                val_loss = criterion(val_logits, y_val_tensor).item()
                val_preds = torch.argmax(val_logits, dim=1).numpy()
                val_acc = np.mean(val_preds == np.array(y_val))

            scheduler.step(val_loss)

            print(f"Epoch {epoch+1}/{self.epochs} | Train: {avg_train_loss:.4f} | Val: {val_loss:.4f} | Acc: {val_acc:.4f}")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_weights = {k: v.clone() for k, v in self.model.state_dict().items()}
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
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


TARGET = "GOOG" 
OTHERS = ["NVDA", "AMZN", "TSLA", "AAPL"]  

def extract_features(data, idx, row):
    """Same feature set per stock — call for each ticker."""
    return [
        row["Close"] / row["moving5"],
        row["Close"] / row["moving10"],
        row["Close"] / row["moving20"],
        row["moving5"] / row["moving20"],
        row["Close"] / data[idx-1]["Close"] - 1,
        row["Close"] / data[idx-5]["Close"]  - 1,
        row["Close"] / data[idx-10]["Close"] - 1,
        row["Close"] / data[idx-20]["Close"] - 1,
        row["RSI"],
        row["GainLoss"],
        row["stochastic"],
        row["adx"],
        row["macd"]       / row["Close"],
        row["macdSignal"] / row["Close"],
        row["macdHist"]   / row["Close"],
        row["Volume"]     / row["moving5"],
    ]

required = ["moving5", "moving10", "moving20", "RSI", "GainLoss",
            "stochastic", "macd", "macdSignal", "macdHist", "adx", "Volume", "Close"]

# --- Fetch and index all stocks by date ---
stock_data = {}  # ticker -> {date_str: (idx, row)}

for ticker in [TARGET] + OTHERS:
    response = requests.get(f"http://127.0.0.1:8000/trades/trades/{ticker}")
    if not response.ok:
        print(f"Failed {ticker}")
        continue
    data = response.json()
    print(f"{ticker}: {len(data)} rows")

    # Label forward returns on target stock only
    if ticker == TARGET:
        for i in range(len(data) - 5):
            y = (data[i+5]['Close'] - data[i]['Close']) / data[i]['Close']
            if y > 0.005:
                data[i]['future'] = "Buy"
            elif y < -0.005:
                data[i]['future'] = "Sell"
            else:
                data[i]['future'] = "Neutral"

    # Index by date so we can align across tickers
    stock_data[ticker] = {row['Date']: (idx, row, data) for idx, row in enumerate(data)}

# --- Build aligned feature rows ---
all_features = []
all_labels   = []

for date, (t_idx, t_row, t_data) in stock_data[TARGET].items():
    if t_idx < 20:
        continue
    if 'future' not in t_row:
        continue
    if not all(k in t_row for k in required):
        continue

    # Check all other stocks also have this date with enough history
    skip = False
    for ticker in OTHERS:
        if ticker not in stock_data:
            skip = True
            break
        if date not in stock_data[ticker]:
            skip = True
            break
        o_idx, o_row, o_data = stock_data[ticker][date]
        if o_idx < 20:
            skip = True
            break
        if not all(k in o_row for k in required):
            skip = True
            break
    if skip:
        continue

    # Target stock features
    row_features = extract_features(t_data, t_idx, t_row)

    # Append other stocks' features for the same date
    for ticker in OTHERS:
        o_idx, o_row, o_data = stock_data[ticker][date]
        row_features += extract_features(o_data, o_idx, o_row)

    all_features.append(row_features)
    all_labels.append(t_row['future'])

print(f"Total aligned samples: {len(all_features)}")
print(f"Features per row: {len(all_features[0])} ({5} stocks × 16 features)")
print(f"Labels: {Counter(all_labels)}")


# =========================
# Preprocessing
# =========================
label_map = {"Sell": 0, "Neutral": 1, "Buy": 2}
y_numeric = np.array([label_map[l] for l in all_labels])

split = int(len(all_features) * 0.8)

X_train_raw = np.array(all_features[:split])
X_test_raw = np.array(all_features[split:])

y_train = y_numeric[:split]
y_test = y_numeric[split:]

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train_raw)
X_test = scaler.transform(X_test_raw)

print("Train:", Counter(y_train))
print("Test:", Counter(y_test))


# =========================
# Class weights
# =========================
class_weights = compute_class_weight('balanced', classes=np.array([0,1,2]), y=y_train)
sample_weights = compute_sample_weight('balanced', y_train)


# =========================
# Train models individually
# =========================
rf = RandomForestClassifier(
    n_estimators=500,
    max_depth=15,
    class_weight='balanced',
    random_state=42
)
rf.fit(X_train, y_train)

xgb = XGBClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.01
)
xgb.fit(X_train, y_train, sample_weight=sample_weights)

lgb = LGBMClassifier(
    n_estimators=500,
    learning_rate=0.01,
    class_weight='balanced'
)
lgb.fit(X_train, y_train)

torch_model = TorchClassifierWrapper(
    input_dim=X_train.shape[1],
    epochs=200,
    batch_size=32,
    lr=0.001,
    class_weights=class_weights
)
torch_model.fit(X_train, y_train)


# =========================
# Ensemble
# =========================
ensemble = VotingClassifier(
    estimators=[
        ('rf', rf),
        ('xgb', xgb),
        ('lgb', lgb),
        ('torch_nn', torch_model)
    ],
    voting='soft'
)

ensemble.fit(X_train, y_train)

print("Ensemble Accuracy:", ensemble.score(X_test, y_test))

preds = ensemble.predict(X_test)

print("Pred dist:", Counter(preds))
print("Actual   :", Counter(y_test))
for name, model in ensemble.named_estimators_.items():
    print(f"{name}: {model.score(X_test, y_test):.4f}")
print(classification_report(y_test, preds, target_names=["Sell", "Neutral", "Buy"]))