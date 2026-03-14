from sklearn.ensemble import RandomForestClassifier
import requests
import requests
from collections import Counter
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.ensemble import VotingClassifier
from lightgbm import LGBMClassifier
api_url = "http://127.0.0.1:8000/trades/trades/AAPL"

def getMovingAvg(data, duration):
    if duration >= len(data):
        return
    print(len(data[:duration]))
    movingSum = sum(item["Close"] for item in data[:duration])
    for i in range(duration, len(data)):
        data[i][f"moving{duration}"] = (movingSum/duration)
        movingSum -= data[i-duration]["Close"]
        movingSum += data[i]["Close"]
    return


response = requests.get(api_url)

if response.ok:
    data = response.json()
    print("API Call Successful!")
    print(f"Data received: {data[0]}")
    print(data[10])
    for i in range(len(data)-1):
        y =  (data[i+1]['Close'] - data[i]['Close'])/data[i]['Close'] 
        print(y)
        if(y > 0.005):
            data[i]['future'] = "Buy"
        elif y < -0.005:
            data[i]['future'] = "Sell"
        else:
            data[i]['future'] = "Neutral"
    print(len(data))
    features = []
    labels = []
    label_counts = Counter(row["future"] for row in data if "future" in row)

    print(label_counts)
 

    for row in data:
        if all(k in row for k in ["moving5","moving10","moving20","RSI","GainLoss","future"]):

            features.append([
                row["Close"],
                # row["High"],
                # row["Low"],
                # row["Open"],
                row["Volume"],
                row["moving5"],
                row["moving10"],
                row["moving20"],
                row["GainLoss"],
                row["RSI"]
            ])

            labels.append(row["future"])
    print(len(features))
    label_map = {"Sell":0, "Neutral":1, "Buy":2}
    y_numeric = [label_map[l] for l in labels]

    X_train, X_test, y_train, y_test = train_test_split(
        features, y_numeric, test_size=0.2, shuffle=False
    )

    model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    random_state=42
)

    model.fit(X_train, y_train)
    accuracy = model.score(X_test, y_test)
    print("Accuracy:", accuracy)
    pred = model.predict(X_test)
    print("Predictions:", Counter(pred))
    print("Actual:", Counter(y_test))



    #gradient boost

    gx_model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05
    )

    gx_model.fit(X_train, y_train)

    print("Accuracy:", gx_model.score(X_test, y_test))

    ensemble = VotingClassifier(
    estimators=[
        ('rf', RandomForestClassifier(n_estimators=300)),
        ('xgb', XGBClassifier(n_estimators=300)),
        ('lgb', LGBMClassifier(n_estimators=300))
    ],
    voting='soft'  # use probabilities
)
    ensemble.fit(X_train, y_train)
    print("Accuracy:",   ensemble.score(X_test, y_test))

else:

    print(f"API Call Failed with status code: {response.status_code}")
    response.raise_for_status() 