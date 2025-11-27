import yfinance as yf
import pandas as pd
import numpy as np
import math

# def simulate_macd_strategy(ticker, year, initial_budget):
ticker = 'TOA.WA'

year = '2025'
initial_budget = 1000

# --- 1. Pobranie danych ---
start_date = f"{year}-01-01"
end_date = f"{year}-12-31"

df = yf.download(ticker, start=start_date, end=end_date)

if df.empty:
    raise ValueError("Brak danych – sprawdź ticker lub zakres dat.")

df.to_csv(f"{ticker}.csv")

df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
df["MACD"] = df["EMA12"] - df["EMA26"]
df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

# sygnały
df["BuySignal"] = ((df["MACD"] > df["Signal"]) & (df["MACD"].shift(1) <= df["Signal"].shift(1))).astype(int)
df["SellSignal"] = ((df["MACD"] < df["Signal"]) & (df["MACD"].shift(1) >= df["Signal"].shift(1))).astype(int)


# --- 3. Symulacja portfela ---
cash = initial_budget
shares = 0
last_buy_cash = None  # zapamiętanie kapitału przed zakupem (do obliczenia zysku)

trades = []

for i in range(len(df) - 1):
    today = df.iloc[i]
    tomorrow = df.iloc[i + 1]

    # --- KUPNO ---
    if today["BuySignal",''] == 1 and cash > 0:
        price = tomorrow["Open",ticker]
        if price > cash:
            continue
        shares = math.floor(cash / price)
        last_buy_cash = cash  # zapamiętujemy ile mieliśmy przed kupnem
        cash -= shares * price  # ile zostało gotówki

        trades.append({
            "date": tomorrow.name,
            "type": "BUY",
            "price": price,
            "shares": shares,
            "cash_after": cash,
            "profit_abs": None,
            "profit_pct": None
        })
        print(trades[-1])

    # --- SPRZEDAŻ ---
    elif today["SellSignal",''] == 1 and shares > 0:
        price = tomorrow["Open",ticker]


        #prevet selling with loss
        if price < trades[-1]['price']:
            continue

        sell_value = shares * price
        cash += sell_value

        # obliczenie zysku od momentu zakupu
        profit_abs = cash - last_buy_cash if last_buy_cash is not None else None
        profit_pct = (profit_abs / last_buy_cash * 100) if last_buy_cash else None

        trades.append({
            "date": tomorrow.name,
            "type": "SELL",
            "price": price,
            "shares": 0,
            "cash_after": cash,
            "profit_abs": profit_abs,
            "profit_pct": profit_pct
        })
        print(trades[-1])

        # shares = 0
        # last_buy_cash = None

# --- 4. Wartość końcowa ---
final_price = df.iloc[-1]["Close",ticker]
final_value = cash + shares * final_price

summary = {
    "ticker": ticker,
    "year": year,
    "initial_budget": initial_budget,
    "final_value": final_value,
    "profit": final_value - initial_budget,
    "return_%": (final_value / initial_budget - 1) * 100,
    "trades": trades
}

    # return summary


# ------------------------------------
# PRZYKŁADOWE URUCHOMIENIE
# ------------------------------------
# result = simulate_macd_strategy("MSFT", 2024, 1000)
result = summary

print("=== PODSUMOWANIE STRATEGII MACD ===")
print(f"Ticker: {result['ticker']}")
print(f"Rok: {result['year']}")
print(f"Kapitał początkowy: {result['initial_budget']}$")
print(f"Wartość końcowa portfela: {result['final_value']:.2f}$")
print(f"Zysk/Strata: {result['profit']}$")
print(f"Zwrot: {result['return_%']}%")

print("\n=== TRANSACJE ===")
for t in result["trades"]:
    date = t["date"].date()
    ttype = t["type"]
    price = t["price"]
    shares = t["shares"]
    cash_after = t["cash_after"]

    print(f"{date} | {ttype} | cena: {price:.2f} | walor: {shares:.4f} | gotówka: {cash_after:.2f}")

    if t["type"] == "SELL":
        print(f"   → Wynik transakcji: {t['profit_abs']:.2f}$ ({t['profit_pct']:.2f}%)")

        