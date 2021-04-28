'''

############### Read Me ###############
 
### Name of strategy: Robot Aiur 1.33

Aiur 1.33 = Aiur 1.32 + logs are saved to a file


### Robot Aiur 1.00 (recap)

Entry rules:
- Long TSLA if it rises more than 5% in the last 5 days.
- Short TSLA if it falls more than 5% in the last 5 days.

Exit rules:
- Take profit of 10%
- Stop loss of 5%

Sizing:
- 1 share per trade.
- We only hold 1 trade at a time.

Assumptions:
- We assume that, before we launch this robot, we are not currently not holding a position on TSLA that was entered by Aiur 1.00 
 
Made by the guys at AlgoTrading101.com

'''

# Docs: https://github.com/alpacahq/alpaca-trade-api-python/tree/cd22b3393aff8df214d867b6a4723a21ea34a3c0

############### Admin Section ###############

import alpaca_trade_api as tradeapi
import time, logging, os


### Step 1: Authentication and connection details

api_key = os.environ.get('my_api_key') # Alpaca API key
api_secret = os.environ.get('my_api_secret') # Alpaca API Secret
base_url = os.environ.get('my_base_url') # Alpaca's base URL
ticker = os.environ.get('ticker_to_trade') # The asset we are trading
current_order_id = int(os.environ.get('order_id')) # Our order id number. Change this if this order id has already been taken
long_percent_change = float(os.environ.get('entry_long_percent_change')) # Percent change of ticker to initate long entry trade
short_percent_change = float(os.environ.get('entry_short_percent_change')) # Percent change of ticker to initate short entry trade
logname = os.environ.get('my_log_name') # Name of the saved log file

### Step 2: Instantiate REST API 

api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')

### Step 3: Create basic logging configuration 

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

## Set logger for saving files
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s', filename=logname, filemode='a')

## Set a logger for display
# Define a Handler which writes messages
console = logging.StreamHandler()
# Write messages of priority INFO or higher
console.setLevel(logging.INFO)
# Set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s')
# Tell the handler to use this format
console.setFormatter(formatter)
# Add the handler to the root logger
logging.getLogger('').addHandler(console)


### Step 4: Set up variables for later use

take_profit_percent = 10  # E.g. 2 means 2% take profit
stop_loss_percent = 5  # E.g. 2 means 2% stop loss

in_long_position = False # We assume we are not in a long position when we start the algo. This should always be false.
in_short_position = False # We assume we are not in a short position when we start the algo. This should always be false.

take_profit_level = None
stop_loss_level = None

risk_per_trade = 1 # How much of your equity to risk per trade

max_position_size_per_order = 5 # (#component1)
max_total_position_size = 50 # (#component2)
max_num_orders_day = 2 # (#component3)

order_tracker = []


############### Functions Section ###############

def check_risk_mgmt(ticker, direction, share_quantity, max_position_size_per_order, max_total_position_size):
    
    original_share_quantity = share_quantity
    
    # Limit order size to specified value. (#component1)
    if share_quantity > max_position_size_per_order:
        share_quantity = max_position_size_per_order 
        logging.warning(f'Order size limit of {max_position_size_per_order} reached.')
        logging.warning(f'Order size reduced from {original_share_quantity} to {share_quantity}.')
        
    # Limit total position we can hold for our ticker (#component2)
    try:
        current_pos = int(api.get_position(ticker).qty)
    except Exception as e:
        if str(e) == 'position does not exist':
            current_pos = 0

    if direction == 'sell':
        attempted_order_size = -share_quantity 
    else:
        attempted_order_size = share_quantity

    if abs(current_pos + attempted_order_size) > max_total_position_size:
        share_quantity = max(max_total_position_size - abs(current_pos), 0)     
        logging.warning(f'Maximum {ticker} position of {max_total_position_size} reached.')
        logging.warning(f'Order size reduced from {original_share_quantity} to {share_quantity}.')

    return share_quantity


def number_of_orders_today(order_tracker, today_date):

    # Check total number of orders today

    num_positions = []
    for stamp in order_tracker:
        if stamp == today_date:
            num_positions.append(True)
    
    logging.info(f'We have entered {len(num_positions)} orders today')
    
    return len(num_positions)
    

def fire_trade(ticker, direction, share_quantity, current_order_id, max_position_size_per_order, max_total_position_size): 
    # Fires a trade (can be an entry or exit). All trades fired are market orders.
    
    share_quantity = check_risk_mgmt(ticker, direction, share_quantity, max_position_size_per_order, max_total_position_size)
    
    if share_quantity > 0:
        
        order_info = api.submit_order(
            symbol=ticker,
            qty=share_quantity,
            side=direction,
            time_in_force='gtc',
            type='market',
            client_order_id='Aiur_' + str(current_order_id),
        )
        time.sleep(3)  # Give it a few seconds to process the order...
    
        if order_info.status == 'accepted':
            
            order_info_status = api.get_order_by_client_order_id('Aiur_' + str(current_order_id)).status
            
            filled_price = api.get_order_by_client_order_id('Aiur_' + str(current_order_id)).filled_avg_price
            
            logging.info(f'Order status for {direction} trade: {order_info_status}')
            logging.info(f'{direction} order price: {filled_price}')
            
            return order_info_status, float(filled_price), share_quantity
                
        else:
        
            logging.warning(f'Order for {direction} trade NOT filled. Status: {order_info.status}')
        
            return order_info.status, None, 0
        
    else:

        return 'Did not fire order', None, 0

def fire_entry_trade(ticker, direction, tp_percent, sl_percent, current_price, risk_per_trade, current_order_id, max_position_size_per_order, max_total_position_size): 
    # All trades fired are market orders. Includes take-profit and stop-loss 
    # Calculate amount of shares to buy 

     # Calculate take-profit and stop-loss
    if direction == 'buy':
        take_profit_level = round(current_price * (1 + tp_percent / 100), 2)  # Calculate take profit level. Round to 2 decimal places
        stop_loss_level = round(current_price * (1 - sl_percent / 100), 2)  # Calculate stop loss level. Round to 2 decimal places

    # Set take-profit and stop-loss
    elif direction == 'sell':
        take_profit_level = round(current_price * (1 - tp_percent / 100),2)  # Calculate take profit level. Round to 2 decimal places
        stop_loss_level = round(current_price * (1 + sl_percent / 100),2)  # Calculate stop loss level. Round to 2 decimal places


    # Calculate position size
    share_quantity = calc_shares(current_price, stop_loss_level, risk_per_trade) 
    
    if share_quantity > 0:

        # Check if entry is allowed
        if entry_allowed(ticker, share_quantity, current_price): # Aiur 1.2 addition

            order_status_new_trade, filled_price, share_quantity_traded = fire_trade(ticker, direction, share_quantity, current_order_id, max_position_size_per_order, max_total_position_size) # Fire a trade

            if order_status_new_trade == 'filled':
                logging.info(f'{direction} entry TP price: {take_profit_level}')
                logging.info(f'{direction} entry SL price: {stop_loss_level}')

            return order_status_new_trade, filled_price, take_profit_level, stop_loss_level, share_quantity_traded

        else:
        
            return 'Did not fire order', None, None, None, 0
    
    else:
        
        return 'Did not fire order', None, None, None, 0
        
def entry_allowed(ticker, share_quantity, current_price): 
    # Check to see if we can't open an entry order due to PDT rule or lack of buying power
    
    # Check to see account is blocked
    account = api.get_account()
    
    if account.pattern_day_trader:
        logging.warning('Account is blocked due to PDT rule. No new entry orders can be fired.')
        return False

    # Check to see if we have enough buying power to execute a trade 
    if float(account.buying_power) < share_quantity * current_price:
        logging.warning(f'Not enough buying power for a entry trade of {share_quantity} shares of {ticker}.')
        return False
    
    return True # Returns True is entry orders are allowed, False otherwise.
  
def wait_for_market_open(): 
    # Check to see if the market is open - wait for open if it is not
    
    clock = api.get_clock()
    if not clock.is_open:
        time_to_open = (clock.next_open - clock.timestamp).total_seconds()
        logging.warning(f'Market is not open, going to sleep for {time_to_open:.2f} seconds')
        time.sleep(time_to_open)
        

def calc_shares(entry_price, stop_price, risk_percent): 
    # Calculate amount of shares to buy 

    account_balances = api.get_account()
    equity = float(account_balances.equity)
    risk_amount = equity * risk_percent / 100    
    risk_per_share = abs(entry_price - stop_price)

    return round(risk_amount / risk_per_share)

############### Strategy Section ###############
    
# Check to see if our asset is tradable before starting main strategy loop 

assets = api.list_assets(status='active')
active_assets = [i.symbol for i in assets]
if ticker not in active_assets:
    logging.error(f'{ticker} is not tradable - halting strategy')
    quit(0)

while True:

    logging.info('--------- Start of current 10 second period ---------')


    ### Step 1: Check to see if the market is open - wait for open if it is not 

    wait_for_market_open()    

    ### Step 2: Get data and calculate required variables
    
    barset = api.get_barset(ticker, 'day', limit=10)  # Get daily price data for TSLA over the last 10 trading days.
    tsla_bars = barset.df[ticker] # Isolate just the bar data for TSLA

    today_close = tsla_bars.close[-1] 
    current_price = today_close # To reduce confusion since today's closing price = current price if today's market session has not ended.
    five_days_ago_close = tsla_bars.close[-6]
    percent_change = ((today_close - five_days_ago_close) / five_days_ago_close * 100)  # Percentage change over the last 5 days

    logging.info(f'{ticker} moved {percent_change:.2f}% over the last 5 days')  

    today_date = tsla_bars.index[-1].date()    

    order_status = None # Reset order status
    order_filled_price = None # Reset order filled price

    ### Step 3: Check to see account is blocked
    account = api.get_account()

    if any([account.account_blocked, account.trading_blocked]):
        logging.warning('Account is blocked - exiting.. ')
        quit(0)

    ### Step 4: Check for exit signal and close our trades if there are exit signals
    
    if in_long_position:
        # We are in a long position - Check for exit
        
        if today_close > take_profit_level or today_close < stop_loss_level: # Check if prices crosses take-profit or stop-loss levels
            order_status, filled_price, share_quantity_exited = fire_trade(ticker, 'sell', share_quantity_entered, current_order_id, max_position_size_per_order, max_total_position_size)
            if order_status == 'filled':
                in_long_position = False
                current_order_id += 1  # Increase client order id by 1
                logging.info(f'We exited our LONG trade of {share_quantity_exited} shares at exit price: {filled_price}!')

    elif in_short_position:
        # We are in a short position - Check for exit
        
        if today_close < take_profit_level or today_close > stop_loss_level: # Check if prices crosses take-profit or stop-loss levels
            order_status, filled_price, share_quantity_exited = fire_trade(ticker, 'buy', share_quantity_entered, current_order_id, max_position_size_per_order, max_total_position_size)
            if order_status == 'filled':
                in_short_position = False
                current_order_id += 1  # Increase client order id by 1
                logging.info(f'We exited our SHORT trade of {share_quantity_exited} shares at exit price: {filled_price}!')
    
      
    ### Step 5: Check for entry signal and enter a new trades if there are entry signals
    
    elif not in_long_position and not in_short_position: 
        # We are not in a position - Look for an entry
        # Insert long entry rule here
        if percent_change > long_percent_change:
            # Long trade signal

            # (#component3)            
            if number_of_orders_today(order_tracker, today_date) < max_num_orders_day:
                
                order_status, filled_price, take_profit_level, stop_loss_level, share_quantity_entered = fire_entry_trade(ticker,
                                                                                                'buy', 
                                                                                                take_profit_percent, 
                                                                                                stop_loss_percent, 
                                                                                                current_price, 
                                                                                                                                                                        risk_per_trade,
                                                                                                                                                                                                current_order_id,
                                                                                               max_position_size_per_order, 
                                                                                               max_total_position_size)

                if order_status == 'filled':
                    in_long_position = True
                    current_order_id += 1  # Increase client order id by 1
                    logging.info(f'We entered a LONG trade of {share_quantity_entered} shares at entry price: {filled_price}!')

                    order_tracker.append(today_date)
                    
            else:
                
                logging.warning(f'Maximum number of orders per day of {max_num_orders_day} is reached.')
                logging.warning(f'Long entry signal triggered but entry order NOT fired.')

        # Insert short entry rule here
        elif percent_change < short_percent_change:
            # Short trade signal

            # (#component3)
            if number_of_orders_today(order_tracker, today_date) < max_num_orders_day:

                order_status, filled_price, take_profit_level, stop_loss_level, share_quantity_entered = fire_entry_trade(ticker,
                                                                                                'sell', 
                                                                                                take_profit_percent, 
                                                                                                stop_loss_percent, 
                                                                                                current_price, 
                                                                                                risk_per_trade,
                                                                                                current_order_id,
                                                                                               max_position_size_per_order, 
                                                                                               max_total_position_size)
                if order_status == 'filled':
                    in_short_position = True
                    current_order_id += 1  # Increase client order id by 1
                    logging.info(f'We entered a SHORT trade of {share_quantity_entered} shares at entry price: {filled_price}!')

                    order_tracker.append(today_date)
                    
            else:
                
                logging.warning(f'Maximum number of orders per day of {max_num_orders_day} is reached.')
                logging.warning(f'Short entry signal triggered but entry order NOT fired.')
                
    
    ### Step 6: Rest for a few seconds before running the Strategy Section again on new price updates

    # Get current positions
    try:
        total_positions_ticker = int(api.get_position(ticker).qty)
    except Exception as e:
        if str(e) == 'position does not exist':
            total_positions_ticker = 0
    
    account = api.get_account()

    logging.info(f'{ticker}\'s current price is {today_close}')
    logging.info(f'We currently hold {total_positions_ticker} shares of {ticker}')
    logging.info(f'Our account equity is ${account.equity}')
    logging.info(f'Our account buying power is ${account.regt_buying_power}')
    logging.info('--------- End of current 10 second period ---------')
    time.sleep(10)  # Rest for 10 seconds
