# ── Stock universe ────────────────────────────────────────────────────────────
# Top 20 constituents of TWSE Taiwan 50 Index (0050)
TAIWAN_50_STOCKS = {
    '2330.TW': {'name': 'TSMC 台積電',           'sector': '半導體'},
    '2317.TW': {'name': '鴻海 Hon Hai',           'sector': '電子製造'},
    '2454.TW': {'name': '聯發科 MediaTek',        'sector': '半導體'},
    '2308.TW': {'name': '台達電 Delta',           'sector': '電子零件'},
    '2382.TW': {'name': '廣達 Quanta',            'sector': '電子製造'},
    '2881.TW': {'name': '富邦金 Fubon',           'sector': '金融'},
    '2882.TW': {'name': '國泰金 Cathay',          'sector': '金融'},
    '6505.TW': {'name': '台塑化 Formosa Petro',   'sector': '石化'},
    '2412.TW': {'name': '中華電 CHT',             'sector': '電信'},
    '1216.TW': {'name': '統一 Uni-President',     'sector': '食品'},
    '2303.TW': {'name': '聯電 UMC',               'sector': '半導體'},
    '2886.TW': {'name': '兆豐金 Mega',            'sector': '金融'},
    '2891.TW': {'name': '中信金 CTBC',            'sector': '金融'},
    '2884.TW': {'name': '玉山金 E.Sun',           'sector': '金融'},
    '5880.TW': {'name': '合庫金 Cooperative',     'sector': '金融'},
    '2002.TW': {'name': '中鋼 China Steel',       'sector': '鋼鐵'},
    '1301.TW': {'name': '台塑 Formosa Plastics',  'sector': '塑化'},
    '1303.TW': {'name': '南亞 Nan Ya',            'sector': '塑化'},
    '2207.TW': {'name': '和泰車 Hotai',           'sector': '汽車'},
    '3711.TW': {'name': '日月光 ASE',             'sector': '半導體封測'},
}

# ── Technical indicator parameters ───────────────────────────────────────────
MA_SHORT         = 20    # Short-term moving average window
MA_LONG          = 60    # Long-term moving average window
RSI_PERIOD       = 14    # RSI lookback period (Wilder's)
VOLATILITY_WINDOW = 30   # Rolling volatility window (days)
LOOKBACK_DAYS    = 365   # Historical data to fetch per ETL run
