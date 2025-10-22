import yfinance as yf
import pandas as pd
import numpy as np
import copy # For deep copying parameter dictionaries

# --- Original Financial Trend Detection Script (Modified) ---
# [Provided by user]

def detect_trend_ema_rsi_sma_adx_obv(symbol='SPY', period='1y', ema_short=8, ema_long=21, rsi_period=14, sma_period=50, adx_period=14, obv_lookback=5, return_score=False):
    """
    Detects the trend for the stock based on multiple indicators.
    Modified to optionally return a numerical score (uptrend_count - downtrend_count).

    Parameters:
        ... (original parameters) ...
        return_score (bool): If True, returns the numerical score instead of the string label.

    Returns:
        String or Int: Trend label (e.g., 'Strong Uptrend') or numerical score (-5 to +5).
    """
    try:
        # Download historical data
        data = yf.download(symbol, period=period, progress=False)

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)


        if data.empty:
            raise ValueError(f"No data downloaded for symbol {symbol}.")

        # --- Indicator Calculations (Identical to original script) ---
        # Calculate EMAs
        data['EMA_Short'] = data['Close'].ewm(span=ema_short, adjust=False).mean()
        data['EMA_Long'] = data['Close'].ewm(span=ema_long, adjust=False).mean()

        # Calculate RSI
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        # Use rolling mean for consistency with ADX calculation style, check NaN handling
        avg_gain = gain.rolling(window=rsi_period, min_periods=rsi_period).mean().fillna(0) # Ensure full window
        avg_loss = loss.rolling(window=rsi_period, min_periods=rsi_period).mean().fillna(0) # Ensure full window
        rs = avg_gain / avg_loss.replace(0, 1e-6) # Avoid division by zero
        data['RSI'] = 100 - (100 / (1 + rs))
        data['RSI'] = data['RSI'].fillna(50) # Fill initial NaNs around 50

        # Calculate SMA
        data['SMA'] = data['Close'].rolling(window=sma_period, min_periods=sma_period).mean() # Ensure full window

        # Calculate ADX (ensure proper NaN handling in intermediate steps)
        high_diff = data['High'].diff().fillna(0)
        low_diff = data['Low'].diff().fillna(0)
        data['Close_Shift'] = data['Close'].shift().fillna(data['Close']) # Handle shift NaN
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0) # Original logic had low_diff > high_diff twice
        
        tr_df = pd.DataFrame({
             'hl': (data['High'] - data['Low']).abs(),
             'hc': (data['High'] - data['Close_Shift']).abs(),
             'lc': (data['Low'] - data['Close_Shift']).abs()
        })
        tr = tr_df.max(axis=1).fillna(0)
        
        # Use EWM for ATR, +DI, -DI smoothing as is common practice and closer to original Wilder's calculation
        atr = tr.ewm(alpha=1/adx_period, adjust=False).mean().replace(0, 1e-6) # Avoid division by zero
        plus_di = 100 * (plus_dm.ewm(alpha=1/adx_period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1/adx_period, adjust=False).mean() / atr)

        dx_num = (plus_di - minus_di).abs()
        dx_den = (plus_di + minus_di).replace(0, 1e-6) # Avoid division by zero
        dx = 100 * (dx_num / dx_den)
        data['ADX'] = dx.ewm(alpha=1/adx_period, adjust=False).mean().fillna(0) # Fill initial NaNs

        data['Plus_DI'] = plus_di.fillna(0)
        data['Minus_DI'] = minus_di.fillna(0)


        # Calculate OBV
        data['OBV'] = (np.sign(data['Close'].diff().fillna(0)) * data['Volume']).fillna(0).cumsum()

        # --- Condition Checks (Using last available valid data point) ---
        last_valid_idx = data.dropna(subset=['EMA_Short', 'EMA_Long', 'RSI', 'SMA', 'ADX', 'Plus_DI', 'Minus_DI', 'OBV']).index[-1]
        last_data = data.loc[last_valid_idx]

        # Use .iloc[-obv_lookback:] for tail, ensure diff() handles start properly
        obv_diff_tail = data['OBV'].diff().fillna(0).iloc[-obv_lookback:]

        # Uptrend conditions
        ema_up = last_data['EMA_Short'] > last_data['EMA_Long']
        rsi_up = last_data['RSI'] > 50
        sma_up = last_data['Close'] > last_data['SMA']
        adx_up = (last_data['ADX'] > 25) and (last_data['Plus_DI'] > last_data['Minus_DI'])
        obv_up = (obv_diff_tail > 0).all() and len(obv_diff_tail) == obv_lookback # Ensure all positive

        # Downtrend conditions
        ema_down = last_data['EMA_Short'] < last_data['EMA_Long']
        rsi_down = last_data['RSI'] < 50
        sma_down = last_data['Close'] < last_data['SMA']
        adx_down = (last_data['ADX'] > 25) and (last_data['Minus_DI'] > last_data['Plus_DI'])
        obv_down = (obv_diff_tail < 0).all() and len(obv_diff_tail) == obv_lookback # Ensure all negative

        # Count true conditions
        uptrend_count = sum([ema_up, rsi_up, sma_up, adx_up, obv_up])
        downtrend_count = sum([ema_down, rsi_down, sma_down, adx_down, obv_down])

        # --- Return Result ---
        if return_score:
            score = uptrend_count - downtrend_count
            # print(f"Debug: Params={ema_short, rsi_period, sma_period, adx_period}, Up={uptrend_count}, Down={downtrend_count}, Score={score}") # Debugging print
            return score
        else:
            # Determine trend string (Identical to original script)
            if uptrend_count >= 5: return "Strong Uptrend"
            elif uptrend_count == 4: return "Better Uptrend"
            elif uptrend_count == 3: return "Uptrend"
            elif downtrend_count >= 5: return "Strong Downtrend"
            elif downtrend_count == 4: return "Better Downtrend"
            elif downtrend_count == 3: return "Downtrend"
            else: return "Consolidation"

    except Exception as e:
        print(f"Error in detect_trend: {e} with params: {symbol, period, ema_short, ema_long, rsi_period, sma_period, adx_period, obv_lookback}")
        # print traceback.format_exc() # For more detailed debugging if needed
        return 0 if return_score else "Error" # Return neutral score on error

# --- MCIK Analysis Functions (Adapted from McikLatticeSimulator) ---

def run_finance_analysis(symbol, period, params):
    """
    Wrapper to run the financial analysis and get the score.
    Ensures parameters are integers where needed.
    """
    # Ensure relevant parameters are integers as required by pandas/ewm/rolling
    int_params = {k: int(round(v)) for k, v in params.items() if k in ['ema_short', 'ema_long', 'rsi_period', 'sma_period', 'adx_period', 'obv_lookback']}
    
    # Check for non-positive window sizes which are invalid
    for k, v in int_params.items():
        if k in ['ema_short', 'ema_long', 'rsi_period', 'sma_period', 'adx_period', 'obv_lookback'] and v <= 0:
            print(f"Warning: Parameter '{k}' has invalid value {v}. Setting to 1.")
            int_params[k] = 1 # Set to a minimal valid value
        # EMA span must be > 1
        if k in ['ema_short', 'ema_long'] and v <= 1:
            print(f"Warning: EMA span parameter '{k}' has invalid value {v}. Setting to 2.")
            int_params[k] = 2

    
    # Merge integer params back into the full dict
    full_params = params.copy()
    full_params.update(int_params)

    score = detect_trend_ema_rsi_sma_adx_obv(
        symbol=symbol,
        period=period,
        return_score=True,
        **full_params # Pass the potentially modified parameters
    )
    return score

def estimate_finance_k_kernel(symbol, period, baseline_params, param_to_poke, poke_delta=1.0):
    """
    Estimates the first-order sensitivity (K kernel) of the trend score
    to a change in a single parameter using finite differences.
    Mimics logic from McikLatticeSimulator.estimate_k_kernel [cite: mcik_lattice_simulator.py].
    """
    print(f"\n--- Estimating K Kernel for Parameter: {param_to_poke} ---")

    # Run Baseline
    print("  - Running Baseline analysis...")
    score_base = run_finance_analysis(symbol, period, baseline_params)
    print(f"    - Baseline Score: {score_base}")

    # Run Poked version
    print(f"  - Running Poked analysis (param: {param_to_poke}, delta: {poke_delta})...")
    params_poked = copy.deepcopy(baseline_params)
    params_poked[param_to_poke] += poke_delta
    score_poked = run_finance_analysis(symbol, period, params_poked)
    print(f"    - Poked Score: {score_poked}")

    # Calculate K [cite: MicroCause_Kernels_Paper_Package.md]
    K = score_poked - score_base
    print(f"  - Estimated K ({param_to_poke}) = {K:.4f}")
    print("--- K Kernel estimation complete ---")
    return K

def estimate_finance_h_kernel(symbol, period, baseline_params, param_a, param_b, poke_delta=1.0):
    """
    Estimates the second-order synergy (H kernel) between two parameters
    using finite differences.
    Mimics logic from McikLatticeSimulator.estimate_h_kernel [cite: mcik_lattice_simulator.py].
    """
    print(f"\n--- Estimating H Kernel for Parameters: {param_a}, {param_b} ---")
    if param_a == param_b:
        print("  - Warning: Parameters are the same. H kernel measures interaction between distinct parameters.")
        # Optionally return zeros or raise error

    # Run Baseline
    print("  - Running Baseline analysis...")
    score_base = run_finance_analysis(symbol, period, baseline_params)
    print(f"    - Baseline Score: {score_base}")

    # Run Poke A
    print(f"  - Running Poke A analysis (param: {param_a}, delta: {poke_delta})...")
    params_a = copy.deepcopy(baseline_params)
    params_a[param_a] += poke_delta
    score_a = run_finance_analysis(symbol, period, params_a)
    print(f"    - Poke A Score: {score_a}")

    # Run Poke B
    print(f"  - Running Poke B analysis (param: {param_b}, delta: {poke_delta})...")
    params_b = copy.deepcopy(baseline_params)
    params_b[param_b] += poke_delta
    score_b = run_finance_analysis(symbol, period, params_b)
    print(f"    - Poke B Score: {score_b}")

    # Run Poke A+B
    print(f"  - Running Poke A+B analysis...")
    params_ab = copy.deepcopy(baseline_params)
    params_ab[param_a] += poke_delta
    params_ab[param_b] += poke_delta
    score_ab = run_finance_analysis(symbol, period, params_ab)
    print(f"    - Poke A+B Score: {score_ab}")

    # Calculate Kernels [cite: MicroCause_Kernels_Paper_Package.md]
    K_a = score_a - score_base
    K_b = score_b - score_base
    score_actual = score_ab - score_base
    score_linear_sum = K_a + K_b
    H_ab = score_actual - score_linear_sum # Synergy term

    print(f"\n  --- Results ---")
    print(f"  - K({param_a}) = {K_a:.4f}")
    print(f"  - K({param_b}) = {K_b:.4f}")
    print(f"  - Expected Linear Sum = {score_linear_sum:.4f}")
    print(f"  - Actual Combined Change = {score_actual:.4f}")
    print(f"  - H({param_a}, {param_b}) [Synergy] = {H_ab:.4f}")
    print("--- H Kernel estimation complete ---")
    return K_a, K_b, H_ab


# --- Example Usage ---
if __name__ == "__main__":
    SYMBOL = 'AAPL' # Apple stock
    PERIOD = '2y'   # Use 2 years of data

    # Define the baseline parameters for the trend detection function
    baseline_parameters = {
        'ema_short': 8,
        'ema_long': 21,
        'rsi_period': 14,
        'sma_period': 50,
        'adx_period': 14,
        'obv_lookback': 5
    }

    print("######################################################")
    print("### MCIK Parameter Sensitivity Analysis for Finance ###")
    print(f"### Symbol: {SYMBOL}, Period: {PERIOD}                ###")
    print("######################################################")

    # --- 1. Get Baseline Trend ---
    print("\n--- Baseline Trend ---")
    baseline_trend = detect_trend_ema_rsi_sma_adx_obv(symbol=SYMBOL, period=PERIOD, **baseline_parameters)
    baseline_score = run_finance_analysis(SYMBOL, PERIOD, baseline_parameters)
    print(f"Baseline Trend String: {baseline_trend}")
    print(f"Baseline Trend Score: {baseline_score}")


    # --- 2. Estimate First-Order Sensitivity (K Kernel) ---
    # How sensitive is the score to changing ema_short by +1?
    K_ema_short = estimate_finance_k_kernel(
        symbol=SYMBOL,
        period=PERIOD,
        baseline_params=baseline_parameters,
        param_to_poke='ema_short',
        poke_delta=1 # Small integer change
    )

    # How sensitive is the score to changing rsi_period by +1?
    K_rsi_period = estimate_finance_k_kernel(
        symbol=SYMBOL,
        period=PERIOD,
        baseline_params=baseline_parameters,
        param_to_poke='rsi_period',
        poke_delta=1
    )


    # --- 3. Estimate Second-Order Synergy (H Kernel) ---
    # Is there synergy between ema_short and rsi_period?
    param1 = 'ema_short'
    param2 = 'rsi_period'
    K1, K2, H_synergy = estimate_finance_h_kernel(
        symbol=SYMBOL,
        period=PERIOD,
        baseline_params=baseline_parameters,
        param_a=param1,
        param_b=param2,
        poke_delta=1 # Use integer delta for periods
    )

    analyze_and_print_synergy(param1, param2, K1, K2, H_synergy)

    # Example: Analyze interaction between SMA and ADX periods
    param3 = 'sma_period'
    param4 = 'adx_period'
    K3, K4, H_synergy_2 = estimate_finance_h_kernel(
        symbol=SYMBOL,
        period=PERIOD,
        baseline_params=baseline_parameters,
        param_a=param3,
        param_b=param4,
        poke_delta=1 # Use integer delta for periods
    )
    
    analyze_and_print_synergy(param3, param4, K3, K4, H_synergy_2)
    # Add interpretation as above...
