# -*- coding: utf-8 -*-
"""
Created on Sat Feb 13 01:41:06 2021

@author: liewl
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Feb 13 01:17:36 2021

@author: liewl
"""

import os, time

temp1 = 'message 1'
TEMP3 = 'message 2'

import logging

logname = os.environ.get('my_log_name')

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s', filename=logname, filemode='a')

while True:
    logging.info(f'Order size limit of {temp1} reached.')
    logging.info(f'Order size limit of {TEMP3} reached.')
    time.sleep(2)

