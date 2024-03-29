'''

############### Read Me ###############
 
### Name of strategy: Robot Aiur 1.40

Aiur 1.40 = Aiur 1.31 + the following components:

- Send in take-profits and stop-loss orders using a bracket order

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
- All orders need to be market orders


Made by the guys at AlgoTrading101.com

'''

# Docs: https://github.com/alpacahq/alpaca-trade-api-python/tree/cd22b3393aff8df214d867b6a4723a21ea34a3c0

############### Admin Section ###############

import alpaca_trade_api as tradeapi
import time
import logging

### Step 1: Authentication and connection details

api_key = '<insert api key>'
api_secret = '<insert secret key>'
base_url = 'https://paper-api.alpaca.markets'


### Step 2: Instantiate REST API 

api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')

### Step 3: Create basic logging configuration 

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')

### Step 4: Set up variables for later use

ticker = 'TSLA' # The asset we are trading

current_order_id = 20200 # Our order id number. Change this if this order id has already been taken

take_profit_percent = 0.3  # E.g. 2 means 2% take profit
stop_loss_percent = 0.3  # E.g. 2 means 2% stop loss

in_long_position = False # We assume we are not in a long position when we start the algo. Set as True if we are in long position.
in_short_position = False # We assume we are not in a short position when we start the algo. Set as True if we are in short position. 

take_profit_level = None
stop_loss_level = None

risk_per_trade = 1 # How much of your equity to risk per trade

max_position_size_per_order = 4 
max_total_position_size = 50 
max_num_orders_day = 2 

order_tracker = []


############### Functions Section ###############


def check_tp_sl_orders(tp_order_id, sl_order_id):
    
    if api.get_order(tp_order_id).status == 'filled':
        logging.info(f'Take-Profit hit. We have exited our trade at {api.get_order(tp_order_id).filled_avg_price}.')
        return 'tp_order_filled'
    
    if api.get_order(sl_order_id).status == 'filled':
        logging.info(f'Stop-Loss hit. We have exited our trade at {api.get_order(sl_order_id).filled_avg_price}.')
        return 'sl_order_filled'
        


def check_risk_mgmt(ticker, direction, share_quantity, max_position_size_per_order, max_total_position_size):
    
    original_share_quantity = share_quantity
    
    # Limit order size to specified value. 
    if share_quantity > max_position_size_per_order:
        share_quantity = max_position_size_per_order 
        logging.warning(f'Order size limit of {max_position_size_per_order} reached.')
        logging.warning(f'Order size reduced from {original_share_quantity} to {share_quantity}.')
        
    # Limit total position we can hold for our ticker 
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
    

def fire_trade(ticker, direction, share_quantity, current_order_id, max_position_size_per_order, max_total_position_size, use_server_tp_sl, take_profit_level, stop_loss_level): 
    # Fires a trade (can be an entry or exit). All trades fired are market orders.
    
    share_quantity = check_risk_mgmt(ticker, direction, share_quantity, max_position_size_per_order, max_total_position_size)
    
    if share_quantity > 0:
        
        if use_server_tp_sl == True:
            
            order_info = api.submit_order(
                symbol=ticker,
                qty=share_quantity,
                side=direction,
                time_in_force='gtc',
                type='market',
                client_order_id='Aiur_' + str(current_order_id),
                order_class='bracket',
                stop_loss=dict(stop_price=str(stop_loss_level)), 
                take_profit=dict(limit_price=str(take_profit_level))
            )
        
        else:
            
            order_info = api.submit_order(
                symbol=ticker,
                qty=share_quantity,
                side=direction,
                time_in_force='gtc',
                type='market',
                client_order_id='Aiur_' + str(current_order_id)
            )
        
        if order_info.status == 'accepted':
            
            if use_server_tp_sl == False:
                tp_order_id = ''
                sl_order_id = ''
            
            if use_server_tp_sl == True and order_info.legs[0].type == 'limit':
                
                tp_order_id = order_info.legs[0].id
                sl_order_id = order_info.legs[1].id
                print(f'TP Order ID: {tp_order_id}')
                print(f'TP Level: {api.get_order(tp_order_id).limit_price}')
                print(f'SL Order ID: {sl_order_id}')
                print(f'SL Level: {api.get_order(sl_order_id).stop_price}')
                 
            elif use_server_tp_sl == True and order_info.legs[0].type == 'stop':
                
                tp_order_id = order_info.legs[1].id
                sl_order_id = order_info.legs[0].id
                print(f'TP Order ID: {tp_order_id}')
                print(f'TP Level: {api.get_order(tp_order_id).limit_price}')
                print(f'SL Order ID: {sl_order_id}')
                print(f'SL Level: {api.get_order(sl_order_id).stop_price}')

            time.sleep(3)  # Give it a few seconds to process the order...

            order_info_status = api.get_order_by_client_order_id('Aiur_' + str(current_order_id)).status
            
            filled_price = api.get_order_by_client_order_id('Aiur_' + str(current_order_id)).filled_avg_price   
            
            logging.info(f'Order status for {direction} trade: {order_info_status}')
            logging.info(f'{direction} order price: {filled_price}')
            
            return order_info_status, float(filled_price), share_quantity, tp_order_id, sl_order_id
                
        else:
            
            logging.warning(f'Order for {direction} trade NOT filled. Status: {order_info.status}')
        
            return order_info.status, None, 0, '', ''
        
    else:
           
        return 'Did not fire order', None, 0, '', ''

def fire_entry_trade(ticker, direction, tp_percent, sl_percent, current_price, risk_per_trade, current_order_id, max_position_size_per_order, max_total_position_size, use_server_tp_sl): 
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
        if entry_allowed(ticker, share_quantity, current_price): 

            order_status_new_trade, filled_price, share_quantity_traded, tp_order_id, sl_order_id = fire_trade(ticker, direction, share_quantity, current_order_id, max_position_size_per_order, max_total_position_size, use_server_tp_sl, take_profit_level, stop_loss_level) # Fire a trade

            if order_status_new_trade == 'filled':
                logging.info(f'{direction} entry TP price: {take_profit_level}')
                logging.info(f'{direction} entry SL price: {stop_loss_level}')

            return order_status_new_trade, filled_price, take_profit_level, stop_loss_level, share_quantity_traded, tp_order_id, sl_order_id

        else:
        
            return 'Did not fire order', None, None, None, 0, None, None 
    
    else:
        
        return 'Did not fire order', None, None, None, 0, None, None
        
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


    ### Step 4a: Check if TP or SL is hit
    
    if in_long_position:
        tp_sl_status = check_tp_sl_orders(tp_order_id, sl_order_id)
        if tp_sl_status == 'tp_order_filled' or tp_sl_status == 'sl_order_filled':
            in_long_position = False
            current_order_id += 1
    elif in_short_position:
        tp_sl_status = check_tp_sl_orders(tp_order_id, sl_order_id)
        if tp_sl_status == 'tp_order_filled' or tp_sl_status == 'sl_order_filled':
            in_short_position = False
            current_order_id += 1
        

    ### Step 4b: Check for exit signal and close our trades if there are exit signals
    
    if in_long_position:
        # We are in a long position - Check for exit
        
        if percent_change < 2: # Insert your exit rules here 
            api.cancel_order(tp_order_id) #  Cancel TP order. Cancelling TP automatically cancels the SL order. We need to remove the TP and SL orders before we can exit our position.
            time.sleep(2) # Give some time for the TP and SL orders to cancel
            order_status, filled_price, share_quantity_exited, tp_order_id, sl_order_id = fire_trade(ticker, 'sell', share_quantity_entered, current_order_id, max_position_size_per_order, max_total_position_size, False, 0, 0) # Last 3 inputs are: use_server_tp_sl, take_profit_level, stop_loss_level. We don't need take-profit and stop-losses here.
            if order_status == 'filled':
                in_long_position = False
                current_order_id += 1  # Increase client order id by 1
                logging.info(f'We exited our LONG trade of {share_quantity_exited} shares at exit price: {filled_price}!')

    elif in_short_position:
        # We are in a short position - Check for exit
        
        if percent_change > 2: # Insert your exit rules here
            api.cancel_order(tp_order_id) #  Cancel TP order. Cancelling TP automatically cancels the SL order. We need to remove the TP and SL orders before we can exit our position.  
            time.sleep(2) # Give some time for the TP and SL orders to cancel
            order_status, filled_price, share_quantity_exited, tp_order_id, sl_order_id = fire_trade(ticker, 'buy', share_quantity_entered, current_order_id, max_position_size_per_order, max_total_position_size, False, 0, 0) # Last 3 inputs are: use_server_tp_sl, take_profit_level, stop_loss_level. We don't need take-profit and stop-losses here.
            if order_status == 'filled':
                in_short_position = False
                current_order_id += 1  # Increase client order id by 1
                logging.info(f'We exited our SHORT trade of {share_quantity_exited} shares at exit price: {filled_price}!')
    
      
    ### Step 5: Check for entry signal and enter a new trades if there are entry signals
    
    elif not in_long_position and not in_short_position: 
        # We are not in a position - Look for an entry
        # Insert long entry rule here
        if percent_change > 5:
            # Long trade signal
         
            if number_of_orders_today(order_tracker, today_date) < max_num_orders_day:
                
                order_status, filled_price, take_profit_level, stop_loss_level, share_quantity_entered, tp_order_id, sl_order_id = fire_entry_trade(ticker,
                                                                                                'buy', 
                                                                                                take_profit_percent, 
                                                                                                stop_loss_percent, 
                                                                                                current_price, 
                                                                                                risk_per_trade,
                                                                                                current_order_id,
                                                                                               max_position_size_per_order, 
                                                                                               max_total_position_size,
                                                                                               True) # Last input is: use_server_tp_sl. We set it as True.

                if order_status == 'filled':
                    in_long_position = True
                    current_order_id += 1  # Increase client order id by 1
                    logging.info(f'We entered a LONG trade of {share_quantity_entered} shares at entry price: {filled_price}!')

                    order_tracker.append(today_date)
                    
            else:
                
                logging.warning(f'Maximum number of orders per day of {max_num_orders_day} is reached.')
                logging.warning(f'Long entry signal triggered but entry order NOT fired.')

        # Insert short entry rule here
        elif percent_change < -5:
            # Short trade signal

            if number_of_orders_today(order_tracker, today_date) < max_num_orders_day:

                order_status, filled_price, take_profit_level, stop_loss_level, share_quantity_entered, tp_order_id, sl_order_id = fire_entry_trade(ticker,
                                                                                                'sell', 
                                                                                                take_profit_percent, 
                                                                                                stop_loss_percent, 
                                                                                                current_price, 
                                                                                                risk_per_trade,
                                                                                                current_order_id,
                                                                                               max_position_size_per_order, 
                                                                                               max_total_position_size,
                                                                                               True) # Last input is: use_server_tp_sl. We set it as True.
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

    try: 
        if tp_order_id != '':
            logging.info(f'We have a TP order on Alpaca\'s server at ${api.get_order(tp_order_id).limit_price}')
    except:
        pass
    
    try: 
        if sl_order_id != '':
            logging.info(f'We have a SL order on Alpaca\'s server at ${api.get_order(sl_order_id).stop_price}')
    except:
        pass
    
    logging.info(f'{ticker}\'s current price is {today_close}')
    logging.info(f'We currently hold {total_positions_ticker} shares of {ticker}')
    logging.info(f'Our account equity is ${account.equity}')
    logging.info(f'Our account buying power is ${account.regt_buying_power}')
    logging.info('--------- End of current 10 second period ---------')
    time.sleep(1)  # Rest for 10 seconds
