
import logging

# Remove current handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

## Set logger for saving logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s', filemode='a', filename='sample2.log')

## Set a logger for display
# Define a Handler which writes messages
handler1 = logging.StreamHandler()
# Write messages of priority INFO or higher
handler1.setLevel(logging.INFO)
# Set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s')
# Tell the handler to use this format
handler1.setFormatter(formatter)
# Add the handler to the root logger
logging.getLogger('').addHandler(handler1)

logging.info('Hellloooo')

