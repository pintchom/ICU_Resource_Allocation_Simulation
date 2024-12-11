################################################################################################################################################
'''
Simulating patient visits for 30 days based on distribution data from Mass General Hospital
'''
################################################################################################################################################
import time
import pandas as pd
import numpy as np
import random as r 
import uuid
import matplotlib.pyplot as plt
################################################################################################################################################
'''Constants'''
t_n = 24 * 60 * 30 # total time in 30 days by minutes (8AM = 0, 8PM = 43200)
tau = 1 # 1 minute arrival intervals
m = 722 # Most recent report number of beds from Mass General Hospital (May 2024)
e = 1.00181 # Growth factor for acceptance threshold
lambd = 0.1 # acceptance threshold
n_day = 1500  # Reduce daily patients to a more realistic number
n = n_day * 30  # Monthly total
average_minutes_in_hospital = 24 * 60  # Reduce average stay to 2.3 days
std_dev_minutes = average_minutes_in_hospital / 2  # Increase variance
people = set() # TODO: set this to set of people
leaving_times = {} # {time: number of people leaving}
order_of_arrivals = {} # {time: [list of people]}
total_u_captured = 0.0
total_u_rejected = 0.0
total_stay_at_home_u = 0.0
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
    age: str
    severity: float # 0-1
    arrival_time: float # 0 -> Time t sub n 
    dispatch_time: float = None # 0 -> Time t sub n 
    status: str = "" # "in bed", "dispatched", "at-home program", "waitlist"
    u: float # Utility
    def __init__(self, id: str, age: str, severity: float, arrival_time: float, dispatch_time: float, u: float = 0.0):
        self.age = age
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
        acceptance_thresholds[i] = acceptance_thresholds[i+1] * (e*(1 + (1 / (m + 1))))
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

    # Determine age group based on severity distribution
    age_rand = r.random()
    cumsum = 0
    age_group = None
    for i, prob in enumerate(distribution_data[severity]):
        cumsum += prob
        if age_rand < cumsum:
            age_group = ['0-17', '18-44', '45-64', '65+'][i]
            break

    # Determine arrival time based on arrival distribution data and day
    day = r.randint(0, 29) # Random day in 30 day period
    arrival_bucket = r.random() * 100
    if arrival_bucket < arrival_times[severity]['0-359']:
        daily_arrival = r.randint(0, 359)
    elif arrival_bucket < arrival_times[severity]['0-359'] + arrival_times[severity]['360 - 839']:
        daily_arrival = r.randint(360, 839)
    else:
        daily_arrival = r.randint(840, 1439)
    
    arrival_time = day * 24 * 60 + daily_arrival # Convert to minutes from start of month
    
    # determine utility 
    if severity == 'urgent':
        u = r.uniform(0.66, 0.99)
        base_duration = average_minutes_in_hospital * r.uniform(0.4, 2.5)
        stay_duration = int(np.random.normal(base_duration, std_dev_minutes * 2))
    elif severity == 'semi_urgent':
        u = r.uniform(0.33, 0.66)
        base_duration = average_minutes_in_hospital * 0.6 * r.uniform(0.4, 2.0) 
        stay_duration = int(np.random.normal(base_duration, std_dev_minutes * 2))
    else:
        u = r.uniform(0, 0.33)
        base_duration = average_minutes_in_hospital * 0.4 * r.uniform(0.4, 2.0)
        stay_duration = int(np.random.normal(base_duration, std_dev_minutes * 2))
    
    # Ensure stay duration is reasonable
    stay_duration = max(30, min(stay_duration, average_minutes_in_hospital * 2))
    
    dispatch_time = arrival_time + stay_duration
    p = Person(str(uuid.uuid4()), age_group, severity, arrival_time, dispatch_time, u)

    if not dispatch_time in leaving_times:
        leaving_times[dispatch_time] = []
    leaving_times[dispatch_time].append(p)

    if arrival_time not in order_of_arrivals:
        order_of_arrivals[arrival_time] = []
    order_of_arrivals[arrival_time].append(p)

    people.add(p)

# Create results list to store data
results = []
utility_over_time = []
rejected_utility_over_time = []
stay_at_home_utility_over_time = []
beds_over_time = []

# Sort arrival times
arrival_times_sorted = sorted(order_of_arrivals.keys())

# Process patients in order of arrival time
# print(leaving_times.keys())
for t in range(t_n):
    if t in leaving_times:
        for p in leaving_times[t]:
            if p.status == "in bed":  # Only free up a bed if the person was actually using one
                m = min(m + 1, 722)  # Don't exceed max capacity
    
    if t not in order_of_arrivals:
        utility_over_time.append(total_u_captured)
        rejected_utility_over_time.append(total_u_rejected)
        stay_at_home_utility_over_time.append(total_stay_at_home_u)
        beds_over_time.append(m)
        continue
        
    for p in order_of_arrivals[t]:
        available_beds = m
        accepted = p.u > acceptance_thresholds[available_beds]
        if m == 0:
            accepted = False
        if accepted:
            p.status = "in bed"
            m -= 1
            total_u_captured += p.u
            decision = "ACCEPTED"
        else:
            total_u_rejected += p.u
            if 0.3 <= p.u <= 0.5:
                p.status = "at-home program"
                total_stay_at_home_u += p.u * 0.75
                decision = "AT-HOME"
            else:
                p.status = "rejected"
                decision = "REJECTED"
        
        # Add result to list
        results.append({
            'person_id': p.id,
            'age': p.age,
            'arrival_time': p.arrival_time,
            'dispatch_time': p.dispatch_time,
            'utility': p.u,
            'decision': decision,
            'remaining_beds': m
        })
    
    utility_over_time.append(total_u_captured)
    rejected_utility_over_time.append(total_u_rejected)
    stay_at_home_utility_over_time.append(total_stay_at_home_u)
    beds_over_time.append(m)

# Create DataFrame and save to CSV
df = pd.DataFrame(results)
df.to_csv('sim_results_1month.csv', index=False)

net_utility = (total_u_captured + total_stay_at_home_u) - total_u_rejected
print(f"Total utility captured: {total_u_captured}")
print(f"Total utility rejected: {total_u_rejected}")
print(f"Total stay-at-home utility: {total_stay_at_home_u}")
print(f"Net utility gain/loss: {net_utility}")

# Plot results
fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(20, 25))

# Plot total utility over time
ax1.plot(utility_over_time, label='Captured Utility')
ax1.plot(rejected_utility_over_time, label='Rejected Utility')
ax1.plot(stay_at_home_utility_over_time, label='Stay-at-Home Utility')
ax1.set_title('Utility Over Time (with growth factor)')
ax1.set_xlabel('Time (minutes)')
ax1.set_ylabel('Total Utility')
ax1.legend()

# Plot available beds over time
ax2.plot(beds_over_time)
ax2.set_title('Available Beds Over Time')
ax2.set_xlabel('Time (minutes)')
ax2.set_ylabel('Number of Beds')

# Plot utility distribution
accepted_utilities = df[df['decision'] == 'ACCEPTED']['utility']
rejected_utilities = df[df['decision'] == 'REJECTED']['utility']
at_home_utilities = df[df['decision'] == 'AT-HOME']['utility']

ax3.hist([accepted_utilities, rejected_utilities, at_home_utilities], bins=50, 
         label=['Accepted', 'Rejected', 'At-Home'], alpha=0.7)
ax3.set_title('Distribution of Patient Utilities')
ax3.set_xlabel('Utility Value')
ax3.set_ylabel('Frequency')
ax3.legend()

# Plot stay at home program utility
ax4.plot(stay_at_home_utility_over_time)
ax4.set_title('Stay-at-Home Program Utility Over Time')
ax4.set_xlabel('Time (minutes)')
ax4.set_ylabel('Total Stay-at-Home Utility')

# Calculate acceptance rates by age group
age_groups = ['0-17', '18-44', '45-64', '65+']
acceptance_rates = []
rejection_rates = []

for age in age_groups:
    age_df = df[df['age'] == age]
    total = len(age_df)
    accepted = len(age_df[age_df['decision'] == 'ACCEPTED'])
    rejected = len(age_df[age_df['decision'] == 'REJECTED'])
    acceptance_rates.append(accepted/total * 100)
    rejection_rates.append(rejected/total * 100)

# Plot acceptance rates by age
x = np.arange(len(age_groups))
width = 0.35

ax5.bar(x - width/2, acceptance_rates, width, label='Accepted')
ax5.bar(x + width/2, rejection_rates, width, label='Rejected')
ax5.set_ylabel('Percentage')
ax5.set_title('Acceptance vs Rejection Rates by Age Group')
ax5.set_xticks(x)
ax5.set_xticklabels(age_groups)
ax5.legend()

# Plot total counts by age and decision
decisions = ['ACCEPTED', 'REJECTED', 'AT-HOME']
age_decision_counts = []
for age in age_groups:
    counts = []
    for decision in decisions:
        count = len(df[(df['age'] == age) & (df['decision'] == decision)])
        counts.append(count)
    age_decision_counts.append(counts)

x = np.arange(len(age_groups))
width = 0.25

ax6.bar(x - width, [counts[0] for counts in age_decision_counts], width, label='Accepted')
ax6.bar(x, [counts[1] for counts in age_decision_counts], width, label='Rejected')
ax6.bar(x + width, [counts[2] for counts in age_decision_counts], width, label='At-Home')
ax6.set_ylabel('Count')
ax6.set_title('Patient Counts by Age Group and Decision')
ax6.set_xticks(x)
ax6.set_xticklabels(age_groups)
ax6.legend()

plt.tight_layout()
plt.savefig('simulation_results.png')
plt.show()

# TODO
'''
- Sort people by arrival time  DONE
- At every time step, take a person IF their arrival time matches DONE
- Fix p.id  Done
- At each time step, check if person is leaving and update remaining beds
- Adjust for month instead of day DONE
- Add more variance 
- Determine better Growth factor 
'''

# TODO: Future Considerations
'''
- Age
- Insurance payment
- More personal sensitive attributes 
'''