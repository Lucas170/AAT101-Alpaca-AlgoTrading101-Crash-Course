
# ############### Read Me ###############
# 
# 
# 
# ## Name of strategy: Robot Aiur 1.11
# 
# Aiur 1.11 = Aiur 1.00 + the following components:
# 
# 1. Use a logging method to print messages with timestamp (#component1) 
# 2. Check if our account is restricted/blocked (#component2)
# 3. Check if we have enough buying power to fire an order (#component3) 
# 4. Check if the market is open (#component4) 
# 5. Check if the asset is tradeable (#component5) 
# 
# 
# 
# 
# 
# ### Robot Aiur 1.00 (recap)
# 
# Entry rules:
# - Long TSLA if it rises more than 5% in the last 5 days.
# - Short TSLA if it falls more than 5% in the last 5 days.
# 
# Exit rules:
# - Take profit of 10%
# - Stop loss of 5%
# 
# Sizing:
# - 1 share per trade.
# - We only hold 1 trade at a time.
# 
# Assumptions:
# - We assume that, before we launch this robot, we are not currently not holding a position on TSLA that was entered by Aiur 1.00 
# 
# 
# 
# Made by the guys at AlgoTrading101.com
# 
# 
# 




# Docs: https://github.com/alpacahq/alpaca-trade-api-python/tree/cd22b3393aff8df214d867b6a4723a21ea34a3c0

############### Admin Section ###############

import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging

### Step 1: Authentication and connection details

api_key = '<insert api_key>'
api_secret = 'insert api_secret'
base_url = 'https://paper-api.alpaca.markets'


### Step 2: Instantiate REST API 

api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')

### Step 3: Create basic logging configuration (#component1) 

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s: %(levelname)s: %(message)s'
)

### Step 4: Set up variables for later use

ticker = 'TSLA' # The asset we are trading

current_order_id = 1596 # Our order id number. Change this if this order id has already been taken

take_profit_percent = 10  # E.g. 2 means 2% take profit
stop_loss_percent = 5  # E.g. 2 means 2% stop loss

in_long_position = False # We assume we are not in a long position when we start the algo. Set as True if we are in long position.
in_short_position = False # We assume we are not in a short position when we start the algo. Set as True if we are in short position. 

take_profit_level = None
stop_loss_level = None

share_quantity = 1



############### Functions Section ###############

# Fires a trade (can be an entry or exit). Only works for Market orders.
def fire_trade(direction): 
    
    order_info = api.submit_order(
        symbol=ticker,
        qty=share_quantity,
        side=direction,
        time_in_force='gtc',
        type='market',
        client_order_id='Aiur_' + str(current_order_id),
    )

    if order_info.status == 'accepted':
        
        time.sleep(3)  # Give it a few seconds to process the order...
        
        order_info_status = api.get_order_by_client_order_id(
            'Aiur_' + str(current_order_id)
        ).status
        
        filled_price = api.get_order_by_client_order_id(
            'Aiur_' + str(current_order_id)
        ).filled_avg_price
        
        logging.info(f'Order status for {direction} trade: {order_info_status}')
        logging.info(f'{direction} order price: {filled_price}')
        
        return order_info_status, float(filled_price)
    
    else:
        
        return order_info.status, None

# Fires a entry trade. Includes take-profit and stop-loss. Only works for Market orders.
def fire_entry_trade(direction, tp_percent, sl_percent): 
    
    order_status_new_trade, filled_price = fire_trade(direction) # Fire a trade
    
    if order_status_new_trade == 'filled':

        # Set take-profit and stop-loss
        if direction == 'buy':
            take_profit_level = round((filled_price * ( 
                1 + tp_percent / 100)), 2 # Round to 2 decimal places
            )  # Calculate take profit level
            stop_loss_level = round((filled_price * (
                1 - sl_percent / 100)), 2 # Round to 2 decimal places
            )  # Calculate stop loss level

        # Set take-profit and stop-loss
        elif direction == 'sell':
            take_profit_level = round((filled_price * (
                1 - tp_percent / 100)), 2 # Round to 2 decimal places
            )  # Calculate take profit level
            stop_loss_level = round((filled_price * (
                1 + sl_percent / 100)), 2 # Round to 2 decimal places
            )  # Calculate stop loss level
                
        logging.info(f'{direction} entry TP price: {take_profit_level}')
        logging.info(f'{direction} entry SL price: {stop_loss_level}')

        return order_status_new_trade, filled_price, take_profit_level, stop_loss_level
    
    else:
        
        return order_status_new_trade, filled_price, 0, 0
    
def entry_allowed(): # Check to see if we can't open an entry order due to PDT rule or lack of buying power
    
    account = api.get_account()
    
    # Check to see account is blocked (#component2)
    
    if account.pattern_day_trader:
        logging.info('Account is blocked due to PDT rule. No new entry orders can be fired.')
        return False

    # Check to see if we have enough buying power to execute a trade (#component3)
    if float(account.buying_power) < share_quantity * today_close:
        logging.info(f'Not enough buying power for a entry trade of {share_quantity} shares of {ticker}.')
        return False
    
    return True # Returns True is entry orders are allowed, False otherwise.
  
def wait_for_market_open(): # Check to see if the market is open - wait for open if it is not (#component4)
    clock = api.get_clock()
    if not clock.is_open:
        time_to_open = (clock.next_open - clock.timestamp).total_seconds()
        logging.info(f'Market is not open, going to sleep for {time_to_open:.2f} seconds')
        time.sleep(time_to_open)





############### Strategy Section ###############
    
# Check to see if our asset is tradable before starting main strategy loop (#component5)

assets = api.list_assets(status='active')
active_assets = [i.symbol for i in assets]
if ticker not in active_assets:
    raise ValueError(f'{ticker} is not tradable - halting strategy')

while True:

    logging.info('--------- Start of current 10 second period ---------')
    logging.info(pd.Timestamp.now())

    ### Step 1: Check to see if the market is open - wait for open if it is not (#component4)

    wait_for_market_open()    

    ### Step 2: Get data and calculate required variables
    
    barset = api.get_barset(ticker, 'day', limit=10)  # Get daily price data for TSLA over the last 10 trading days.
    tsla_bars = barset.df[ticker]

    today_close = tsla_bars['close'][-1] 
    five_days_ago_close = tsla_bars['close'][-6]
    percent_change = ((today_close - five_days_ago_close) / five_days_ago_close * 100)  # Percentage change over the last 5 days

    logging.info(f'{ticker} moved {percent_change:.2f}% over the last 5 days')  
    
    order_status = None # Reset order status
    order_filled_price = None # Reset order filled price

    ### Step 3: Check to see account is blocked (#component2)
    account = api.get_account()

    if any([account.account_blocked, account.trading_blocked]):
        raise Exception('Account is blocked - exiting.. ')

    ### Step 4: Check for exit signal and close our trades if there are exit signals
    
    if in_long_position:
        # We are in a long position - Check for exit
        if today_close > take_profit_level or today_close < stop_loss_level: # Check if prices crosses take-profit or stop-loss levels
            order_status, filled_price = fire_trade('sell')
            if order_status == 'filled':
                in_long_position = False
                current_order_id += 1  # Increase client order id by 1
                logging.info(f'We exited our LONG trade at exit price: {filled_price}!')

    elif in_short_position:
        # We are in a short position - Check for exit
        if today_close < take_profit_level or today_close > stop_loss_level: # Check if prices crosses take-profit or stop-loss levels
            order_status, filled_price = fire_trade('buy')
            if order_status == 'filled':
                in_short_position = False
                current_order_id += 1  # Increase client order id by 1
                logging.info(f'We exited our SHORT trade at exit price: {filled_price}!')
    
      
    ### Step 5: Check for entry signal and enter a new trades if there are entry signals
    
    elif not in_long_position and not in_short_position: 
        
        # We are not in a position - Look for an entry. 
        # Insert long entry rule here
        if percent_change > 5 and entry_allowed(): # (#component3)
            # Long trade signal - open trade
            order_status, filled_price, take_profit_level, stop_loss_level = fire_entry_trade('buy', take_profit_percent, stop_loss_percent)
            if order_status == 'filled':
                in_long_position = True
                current_order_id += 1  # Increase client order id by 1
                logging.info(f'We entered a LONG trade at entry price: {filled_price}!')

        # Insert short entry rule here  
        elif percent_change < -5 and entry_allowed(): # (#component3)
            # Short trade signal - Open trade
            order_status, filled_price, take_profit_level, stop_loss_level = fire_entry_trade('sell', take_profit_percent, stop_loss_percent)
            if order_status == 'filled':
                in_short_position = True
                current_order_id += 1  # Increase client order id by 1
                logging.info(f'We entered a SHORT trade at entry price: {filled_price}!')
                
    
    ### Step 6: Rest for a few seconds before running the Strategy Section again on new price updates
    
    logging.info(f'{ticker}\'s current price is {today_close}')
    logging.info('--------- End of current 10 second period ---------')
    time.sleep(10)  # Rest for 10 seconds





