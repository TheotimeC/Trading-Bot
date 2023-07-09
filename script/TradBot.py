import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import requests
import time
import mpld3
# Fonction pour récupérer les données historiques de l'ETH depuis l'API Binance
def get_eth_data():
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "ETHUSDT",
        "interval": "15m",
        "limit": 1000  # Nombre de bougies à récupérer (max 1000)
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Convertir les données en DataFrame
    df = pd.DataFrame(data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTime', 'QuoteVolume',
                                     'TradesCount', 'TakerBuyBaseVolume', 'TakerBuyQuoteVolume', 'Ignore'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df.set_index('Timestamp', inplace=True)
    df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
    
    return df

# Fonction pour calculer l'indicateur RSI
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    average_gain = gain.rolling(window).mean()
    average_loss = loss.rolling(window).mean()
    relative_strength = average_gain / average_loss
    rsi = 100 - (100 / (1 + relative_strength))
    return rsi

# Fonction de mise à jour du graphique
def update_chart():
    recent_data = get_eth_data().tail(1)
    recent_rsi = calculate_rsi(recent_data)
    recent_signal = np.where(recent_rsi > 70, -1.0, 0.0)
    recent_signal = np.where(recent_rsi < 30, 1.0, recent_signal)
    recent_position = recent_signal[0] - data['Signal'].iloc[-1]
    recent_close = recent_data['Close'].iloc[0]
    recent_portfolio_value = recent_position * recent_close
    recent_balance = data['Balance'].iloc[-1] + recent_portfolio_value
    recent_smoothed_balance = data['SmoothedBalance'].iloc[-1] * 0.9 + recent_balance * 0.1

    data.loc[recent_data.index, 'RSI'] = recent_rsi
    data.loc[recent_data.index, 'Signal'] = recent_signal
    data.loc[recent_data.index, 'Position'] = recent_position
    data.loc[recent_data.index, 'Close'] = recent_close
    data.loc[recent_data.index, 'PortfolioValue'] = recent_portfolio_value
    data.loc[recent_data.index, 'Balance'] = recent_balance
    data.loc[recent_data.index, 'SmoothedBalance'] = recent_smoothed_balance

    # Initialiser le graphique
    fig, ax = plt.subplots(figsize=(12, 8))

    # Tracer votre graphique ici
    ax.plot(data.index, data['Close'], label='Prix')
    ax.plot(data.loc[data['Position'] == 1.0].index, data['Close'][data['Position'] == 1.0],
            '^', markersize=10, color='g', label='Achat')
    ax.plot(data.loc[data['Position'] == -1.0].index, data['Close'][data['Position'] == -1.0],
            'v', markersize=10, color='r', label='Vente')
    ax.set_ylabel("Prix de l'ETH ($)")
    ax.set_title("Variations de l'ETH")
    ax.legend()

    # Activer le support de mpld3 pour le zoom et le pan
    mpld3.plugins.connect(fig, mpld3.plugins.Zoom())
    #mpld3.plugins.connect(fig, mpld3.plugins.Pan())

    # Afficher le graphique interactif
    mpld3.save_html(fig, 'D:/TradingBot/Trading-Bot/Graph/graph.html')

# Initialiser le graphique
plt.figure(figsize=(12, 8))

# Mettre à jour le graphique toutes les 2 minutes
ani = FuncAnimation(plt.gcf(), update_chart, interval=5000)


while True:
    # Initialiser le graphique
    plt.figure(figsize=(12, 8))

    # Récupérer les données historiques de l'ETH depuis l'API Binance
    data = get_eth_data()

    # Calculer l'indicateur RSI
    data['RSI'] = calculate_rsi(data)

    # Afficher les données
    print(data)

    # Définir le montant initial du capital de trading
    capital = 10000  # Montant initial du capital en dollars

    # Générer les signaux de trading en fonction de l'indicateur RSI
    data['Signal'] = 0.0
    data['Signal'] = np.where(data['RSI'] > 70, -1.0, 0.0)  # Vendre si RSI est supérieur à 70
    data['Signal'] = np.where(data['RSI'] < 30, 1.0, data['Signal'])  # Acheter si RSI est inférieur à 30

    # Générer les positions (acheter/vendre) en fonction des signaux de trading
    data['Position'] = data['Signal'].diff()

    # Ajouter une colonne pour suivre la valeur du portefeuille en fonction des positions de trading
    data['PortfolioValue'] = data['Position'] * data['Close']  # Valeur du portefeuille en fonction des positions de trading

    # Calculer le solde du portefeuille
    data['Balance'] = capital + data['PortfolioValue'].cumsum()

    # Lissage du graphique du solde du portefeuille avec une moyenne mobile exponentielle
    data['SmoothedBalance'] = data['Balance'].ewm(span=30, adjust=False).mean()

    plt.plot(data.index, data['SmoothedBalance'], color='r', label='Solde du portefeuille')
    plt.ylabel('Solde du portefeuille ($)')
    plt.xlabel('Date')
    plt.title('Évolution du solde du portefeuille')

# Enregistrer le graphique sous forme de fichier HTML
    mpld3.save_html(plt.gcf(), 'D:/TradingBot/Trading-Bot/Graph/portfolio.html')
    # Mettre à jour le graphique
    update_chart()

    
    # Attendre pendant l'intervalle souhaité (par exemple, 15 minutes)
    time.sleep(5)  # 900 secondes = 15 minutes


