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

import os
temp1 = os.environ.get('tempa')
TEMP3 = os.environ.get('tempb')

import logging

temp1 = 'temp1 print'
TEMP3 = 'temp3 print'

print(temp1)

print(TEMP3)


logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')

logging.info(temp1)

logging.info(TEMP3)



print(f'Order size limit of {temp1} reached.')
print(f'Order size limit of {TEMP3} reached.')