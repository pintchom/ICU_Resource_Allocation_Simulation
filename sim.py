################################################################################################################################################
'''
Simulating patient visits for 30 day based on distribution data from Mass General Hospital
'''
################################################################################################################################################
import time
import pandas as pd
import numpy as np
import random as r 
import uuid
################################################################################################################################################
'''Constants'''
t_n = 24 * 60 # * 30 # total time in a day by minutes (8AM = 0, 8PM = 1440)
tau = 1 # 1 minute arrival intervals
m = 722 # Most recent report number of beds from Mass General Hospital (May 2024)
e = 1.00181 # Growth factor for acceptance threshold
lambd = 0.1 # acceptance threshold
n = 12174 # (Jan 2023 average monthly visitors)
n_day = n / 30 # Average daily visitors
people = set() # TODO: set this to set of people
leaving_times = {} # {time: number of people leaving}
average_minutes_in_hospital =  457.1337082 # Average minutes in hospital from Mass General Hospital (May 2024)
# TODO: Fluctuate average stay based on severity
total_u_captured = 0.0
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

arrival_times = {
    'urgent': {
        '0-359': 43.3,
        '360 - 839': 41.3,
        '840 - 1439': 15.5,
    },
    'semi_urgent': {
        '0-359': 43.5,
        '360 - 839': 42.8,
        '840 - 1439': 13.7,
    },
    'non_urgent': {
        '0-359': 45.7,
        '360 - 839': 41.3,
        '840 - 1439': 13.0,
    }
}
################################################################################################################################################
'''Person Class'''
class Person:
    id: str
    # age: int
    severity: float # 0-1
    arrival_time: float # 0 -> Time t sub n 
    dispatch_time: float = None # 0 -> Time t sub n 
    status: str = "" # "in bed", "dispatched", "at-home program", "waitlist"
    u: float # Utility
    def __init__(self, severity: float, arrival_time: float, dispatch_time: float, u: float = 0.0, id: str = str(uuid.uuid4())):
        # self.age = age
        self.severity = severity
        self.arrival_time = arrival_time
        self.dispatch_time = dispatch_time
        self.u = u
        self.id = id

    def change_status(self, new_status: str):
        self.status = new_status

    def set_dispatch_time(self, dispatch_time: float):
        self.dispatch_time = dispatch_time
################################################################################################################################################
'''Determine acceptance thresholds for each bed count'''
acceptance_thresholds = {} # when beds available = x, acceptance threshold = acceptance_thresholds[x]
for i in range(m, -1, -1):
    if i == m:
        acceptance_thresholds[i] = 0.1
    else:
        acceptance_thresholds[i] = acceptance_thresholds[i+1] * ((1 + (1 / (m + 1))))
# print(acceptance_thresholds)
################################################################################################################################################
'''Generate Patients'''
for _ in range(n):
    # Determine urgency level
    severity = r.random()
    if severity < overall_probs['urgent']:
        severity = 'urgent'
    elif severity < overall_probs['urgent'] + overall_probs['semi_urgent']:
        severity = 'semi_urgent'
    else:
        severity = 'non_urgent'

    # Determine arrival time based on arrival distribution data
    arrival_bucket = r.random() * 100
    if arrival_bucket < arrival_times[severity]['0-359']:
        arrival_time = r.randint(0, 359)
    elif arrival_bucket < arrival_times[severity]['0-359'] + arrival_times[severity]['360 - 839']:
        arrival_time = r.randint(360, 839)
    else:
        arrival_time = r.randint(840, 1439)
    
    # determine utility 
    if severity == 'urgent':
        u = r.uniform(0.66, 0.99)
    elif severity == 'semi_urgent':
        u = r.uniform(0.33, 0.66)
    else:
        u = r.uniform(0, 0.33)
    
    p = Person(severity, arrival_time, None, u)
    people.add(p)

# Create results list to store data
results = []

for t in range(t_n):
    p = r.choice(list(people))  # Convert set to list for random selection
    available_beds = m 
    accepted = p.u > acceptance_thresholds[available_beds]
    if m == 0:
        accepted = False
    if accepted:
        print(f"{p.id} ACCEPTED !!! 🎉")
        print(f"New remaining beds: {m}")
        m -= 1
        total_u_captured += p.u
        decision = "ACCEPTED"
    else:
        print(f"{p.id} REJECTED !!! 😡")
        print(f"New remaining beds: {m}")
        decision = "REJECTED"
    print()
    
    # Add result to list
    results.append({
        'person_id': p.id,
        'arrival_time': p.arrival_time,
        'utility': p.u,
        'decision': decision,
        'remaining_beds': m
    })

# Create DataFrame and save to CSV
df = pd.DataFrame(results)
df.to_csv('sim_results.csv', index=False)

print(f"Total utility captured: {total_u_captured}")

# TODO
'''
- Sort people by arrival time 
- At every time step, take a person IF their arrival time matches 
- Fix p.id 
- At each time step, check if person is leaving and update remaining beds
- Adjust for month instead of day 
- Add more variance 
- Determine better Growth factor 
'''