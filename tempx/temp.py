# -*- coding: utf-8 -*-
"""
Created on Sat Feb 13 01:17:36 2021

@author: liewl
"""
import logging

temp1 = 'temp1 print'
temp2

print(temp1)
print(temp2)

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')

logging.info(temp1)
logging.info(temp2)


