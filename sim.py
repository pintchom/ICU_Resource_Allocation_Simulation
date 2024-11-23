################################################################################################################################################
'''
Simulating patient visits for 30 day based on distribution data from Mass General Hospital
'''
################################################################################################################################################
import time
import pandas as pd
import numpy as np
import random as r 
################################################################################################################################################
'''Constants'''
t_n = 24 * 60 # total time in a day by minutes
tau = 1 # 1 minute arrival intervals
m = 721.9354839 # Most recent report number of beds from Mass General Hospital (May 2024)
e = 1.2 # Growth factor for acceptance threshold
lambd = 0.1 # acceptance threshold
n = 12174 # (Jan 2023 average monthly visitors)
n_day = n / 30 # Average daily visitors
people = set() # TODO: set this to set of people
average_minutes_in_hospital =  457.1337082 # Average minutes in hospital from Mass General Hospital (May 2024)
# TODO: Fluctuate average stay based on severity
################################################################################################################################################
'''Distribution Data'''
distribution_data = { # Per age group
    # Severity: [0-17, 18-44, 45-64, 65+]
    'urgent': [0.19, 0.403, 0.219, 0.188],
    'semi_urgent': [0.283, 0.446, 0.175, 0.096], 
    'non_urgent': [0.277, 0.469, 0.173, 0.081]
}

overall_probs = { # Overall probability of each urgency level
    'urgent': 0.612,
    'semi_urgent': 0.287,
    'non_urgent': 0.101
}
################################################################################################################################################
'''Person Class'''
class Person:
    age: int
    severity: float # 0-1
    arrival_time: float # 0 -> Time t sub n 
    dispatch_time: float = None # 0 -> Time t sub n 
    status: str = "" # "in bed", "dispatched", "at-home program", "waitlist"
    
    def __init__(self, age: int, severity: float, arrival_time: float, dispatch_time: float):
        self.age = age
        self.severity = severity
        self.arrival_time = arrival_time
        self.dispatch_time = dispatch_time

    def change_status(self, new_status: str):
        self.status = new_status

    def set_dispatch_time(self, dispatch_time: float):
        self.dispatch_time = dispatch_time

################################################################################################################################################
'''Generate Patients'''
for _ in range(n):
    pass