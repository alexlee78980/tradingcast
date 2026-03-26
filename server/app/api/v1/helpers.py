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
def getStochastic(data, period=14):
    print(data[0])
    for i in range(period, len(data)):
        # Use 'd' to access each item in the period slice
        highest = max(float(d["High"]) for d in data[i-period:i])
        lowest = min(float(d["Low"]) for d in data[i-period:i])

        close = float(data[i]["Close"])

        if highest - lowest == 0:
            data[i]["stochastic"] = 0
        else:
            data[i]["stochastic"] = ((close - lowest) / (highest - lowest)) * 100

def getMACD(data, short=12, long=26, signal_period=9):

    multiplier_short = 2 / (short + 1)
    multiplier_long = 2 / (long + 1)
    multiplier_signal = 2 / (signal_period + 1)

    ema_short = data[0]["Close"]
    ema_long = data[0]["Close"]

    macd_list = []
    signal = 0

    for i in range(len(data)):

        close = data[i]["Close"]

        ema_short = (close - ema_short) * multiplier_short + ema_short
        ema_long = (close - ema_long) * multiplier_long + ema_long

        macd = ema_short - ema_long
        macd_list.append(macd)

        if i == 0:
            signal = macd
        else:
            signal = (macd - signal) * multiplier_signal + signal

        data[i]["macd"] = macd
        data[i]["macdSignal"] = signal
        data[i]["macdHist"] = macd - signal

def getADX(data, period=14):

    tr_list = []
    plus_dm_list = []
    minus_dm_list = []

    for i in range(1, len(data)):

        high = data[i]["High"]
        low = data[i]["Low"]
        prev_close = data[i-1]["Close"]

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )

        up_move = high - data[i-1]["High"]
        down_move = data[i-1]["Low"] - low

        plus_dm = up_move if up_move > down_move and up_move > 0 else 0
        minus_dm = down_move if down_move > up_move and down_move > 0 else 0

        tr_list.append(tr)
        plus_dm_list.append(plus_dm)
        minus_dm_list.append(minus_dm)

    for i in range(period, len(tr_list)):

        tr_sum = sum(tr_list[i-period:i])
        plus_dm_sum = sum(plus_dm_list[i-period:i])
        minus_dm_sum = sum(minus_dm_list[i-period:i])

        if tr_sum == 0:
            data[i]["adx"] = 0
            continue

        plus_di = 100 * (plus_dm_sum / tr_sum)
        minus_di = 100 * (minus_dm_sum / tr_sum)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) != 0 else 0

        data[i]["adx"] = dx

def getRSI(data, duration=14):
    sofarLoss = 0
    sofarGain = 0
    rsi_values = []

    data[0]["GainLoss"] = 0

    for i in range(1, len(data)):
        change = data[i]["Close"] - data[i-1]["Close"]
        data[i]["GainLoss"] = change

        gain = max(change, 0)
        loss = max(-change, 0)

        sofarGain += gain
        sofarLoss += loss

        if i > duration:
            oldest_change = data[i-duration]["GainLoss"]

            if oldest_change > 0:
                sofarGain -= oldest_change
            else:
                sofarLoss -= abs(oldest_change)

        if i >= duration:
            avg_gain = sofarGain / duration
            avg_loss = sofarLoss / duration

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            data[i]["RSI"] = rsi
            rsi_values.append(rsi)

    return rsi_values


def add_extra_features(data: list) -> list:
    closes  = [row['Close'] for row in data]
    highs   = [row['High'] for row in data]
    lows    = [row['Low'] for row in data]
    volumes = [row['Volume'] for row in data]

    for i, row in enumerate(data):

        # ── 52 week high/low (252 trading days) ──────────────────────
        start_252 = max(0, i - 252)
        high_252  = max(closes[start_252:i+1])
        low_252   = min(closes[start_252:i+1])
        row['distance_from_52w_high'] = round(row['Close'] / high_252, 4) if high_252 else 0
        row['distance_from_52w_low']  = round(row['Close'] / low_252, 4)  if low_252  else 0

        # ── volume ratio (today vs 20 day avg) ───────────────────────
        start_20 = max(0, i - 20)
        avg_volume_20 = sum(volumes[start_20:i+1]) / len(volumes[start_20:i+1])
        row['volume_ratio'] = round(row['Volume'] / avg_volume_20, 4) if avg_volume_20 else 0

        # ── ATR - average true range (14 days) ───────────────────────
        if i == 0:
            row['atr'] = highs[i] - lows[i]
        else:
            true_ranges = []
            for j in range(max(1, i - 13), i + 1):
                high_low   = highs[j] - lows[j]
                high_close = abs(highs[j] - closes[j-1])
                low_close  = abs(lows[j] - closes[j-1])
                true_ranges.append(max(high_low, high_close, low_close))
            row['atr'] = round(sum(true_ranges) / len(true_ranges), 4)

        # ── price vs MA50 ─────────────────────────────────────────────
        start_50 = max(0, i - 49)
        ma50 = sum(closes[start_50:i+1]) / len(closes[start_50:i+1])
        row['price_vs_ma50'] = round(row['Close'] / ma50, 4) if ma50 else 0

        # ── price vs MA200 ────────────────────────────────────────────
        start_200 = max(0, i - 199)
        ma200 = sum(closes[start_200:i+1]) / len(closes[start_200:i+1])
        row['price_vs_ma200'] = round(row['Close'] / ma200, 4) if ma200 else 0

    return data