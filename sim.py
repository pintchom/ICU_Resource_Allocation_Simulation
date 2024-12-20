################################################################################################################################################
'''
Simulating patient visits for 30 days based on distribution data from Mass General Hospital
Comparing utility-based acceptance vs first-come-first-served
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
e = 1.00165 # Growth factor for acceptance threshold
lambd = 0.01 # acceptance threshold
n_day = 1000  # Reduce daily patients to a more realistic number
n = n_day * 30  # Monthly total
average_minutes_in_hospital = 14.1*60  # Reduce average stay to 2.3 days
std_dev_minutes = average_minutes_in_hospital / 2  # Increase variance
people = set() # TODO: set this to set of people
leaving_times = {} # {time: number of people leaving}
order_of_arrivals = {} # {time: [list of people]}
total_u_captured = 0.0
total_u_rejected = 0.0
total_stay_at_home_u = 0.0

# For FCFS comparison
fcfs_u_captured = 0.0
fcfs_u_rejected = 0.0
fcfs_stay_at_home_u = 0.0

# For tracking accepted/rejected utilities in FCFS
fcfs_accepted_utilities = []
fcfs_rejected_utilities = []
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
    def __init__(self, id: str, severity: float, arrival_time: float, dispatch_time: float, u: float = 0.0):
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
        acceptance_thresholds[i] = acceptance_thresholds[i+1] * (e * (1 + (1 / (m + 1))))
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
        base_duration = average_minutes_in_hospital * 0.66 * r.uniform(0.4, 2.0) 
        stay_duration = int(np.random.normal(base_duration, std_dev_minutes * 2))
    else:
        u = r.uniform(0, 0.33)
        base_duration = average_minutes_in_hospital * 0.33 * r.uniform(0.4, 2.0)
        stay_duration = int(np.random.normal(base_duration, std_dev_minutes * 2))
    
    # Ensure stay duration is reasonable
    stay_duration = max(30, stay_duration)
    
    dispatch_time = arrival_time + stay_duration
    p = Person(str(uuid.uuid4()), severity, arrival_time, dispatch_time, u)

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

# For FCFS comparison
fcfs_utility_over_time = []
fcfs_rejected_utility_over_time = []
fcfs_stay_at_home_utility_over_time = []
fcfs_beds_over_time = []

# Sort arrival times
arrival_times_sorted = sorted(order_of_arrivals.keys())

# Process patients in order of arrival time - Utility-based approach
m_utility = m  # Separate bed counter for utility-based approach
for t in range(t_n):
    if t in leaving_times:
        for p in leaving_times[t]:
            if p.status == "in bed":  # Only free up a bed if the person was actually using one
                m_utility = min(m_utility + 1, 722)  # Don't exceed max capacity
    
    if t not in order_of_arrivals:
        utility_over_time.append(total_u_captured)
        rejected_utility_over_time.append(total_u_rejected)
        stay_at_home_utility_over_time.append(total_stay_at_home_u)
        beds_over_time.append(m_utility)
        continue
        
    for p in order_of_arrivals[t]:
        available_beds = m_utility
        accepted = p.u > acceptance_thresholds[available_beds]
        if m_utility == 0:
            accepted = False
        if accepted:
            p.status = "in bed"
            m_utility -= 1
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
            'arrival_time': p.arrival_time,
            'dispatch_time': p.dispatch_time,
            'utility': p.u,
            'decision': decision,
            'remaining_beds': m_utility
        })
    
    utility_over_time.append(total_u_captured)
    rejected_utility_over_time.append(total_u_rejected)
    stay_at_home_utility_over_time.append(total_stay_at_home_u)
    beds_over_time.append(m_utility)

# Process patients in order of arrival time - FCFS approach
m_fcfs = m  # Separate bed counter for FCFS
for t in range(t_n):
    if t in leaving_times:
        for p in leaving_times[t]:
            if p.status == "in bed (FCFS)":
                m_fcfs = min(m_fcfs + 1, 722)
    
    if t in order_of_arrivals:
        for p in order_of_arrivals[t]:
            if m_fcfs > 0:  # If beds available, accept patient
                p.status = "in bed (FCFS)"
                m_fcfs -= 1
                fcfs_u_captured += p.u
                fcfs_accepted_utilities.append(p.u)
            else:  # No beds available
                fcfs_u_rejected += p.u
                fcfs_rejected_utilities.append(p.u)
                if 0.3 <= p.u <= 0.5:
                    p.status = "at-home program (FCFS)"
                    fcfs_stay_at_home_u += p.u * 0.75
    
    fcfs_utility_over_time.append(fcfs_u_captured)
    fcfs_rejected_utility_over_time.append(fcfs_u_rejected)
    fcfs_stay_at_home_utility_over_time.append(fcfs_stay_at_home_u)
    fcfs_beds_over_time.append(m_fcfs)

# Create DataFrame and save to CSV
df = pd.DataFrame(results)
df.to_csv('sim_results_1month.csv', index=False)

# Calculate net utilities
net_utility = (total_u_captured + total_stay_at_home_u) - total_u_rejected
fcfs_net_utility = (fcfs_u_captured + fcfs_stay_at_home_u) - fcfs_u_rejected

print("\nUtility-based approach results:")
print(f"Total utility captured: {total_u_captured:.2f}")
print(f"Total utility rejected: {total_u_rejected:.2f}")
print(f"Total stay-at-home utility: {total_stay_at_home_u:.2f}")
print(f"Net utility gain/loss: {net_utility:.2f}")

print("\nFirst-Come-First-Served approach results:")
print(f"Total utility captured: {fcfs_u_captured:.2f}")
print(f"Total utility rejected: {fcfs_u_rejected:.2f}")
print(f"Total stay-at-home utility: {fcfs_stay_at_home_u:.2f}")
print(f"Net utility gain/loss: {fcfs_net_utility:.2f}")

if net_utility > fcfs_net_utility:
    print(f"\nUtility-based approach performed {((net_utility/fcfs_net_utility) - 1)*100:.1f}% better than FCFS")
elif net_utility < fcfs_net_utility:
    print(f"\nUtility-based approach performed {(1 - abs(net_utility/fcfs_net_utility))*100:.1f}% worse than FCFS") 
else:
    print("\nBoth approaches performed equally")

# Plot results
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 15))

# Plot total utility over time for both approaches
ax1.plot(utility_over_time, label='Utility-based Captured')
ax1.plot(fcfs_utility_over_time, label='FCFS Captured', linestyle='--')
ax1.set_title('Captured Utility Over Time')
ax1.set_xlabel('Time (minutes)')
ax1.set_ylabel('Total Utility')
ax1.legend()

# Plot available beds over time for both approaches
ax2.plot(beds_over_time, label='Utility-based')
ax2.plot(fcfs_beds_over_time, label='FCFS', linestyle='--')
ax2.set_title('Available Beds Over Time')
ax2.set_xlabel('Time (minutes)')
ax2.set_ylabel('Number of Beds')
ax2.legend()

# Plot utility distributions for both approaches
utility_accepted = df[df['decision'] == 'ACCEPTED']['utility']
utility_rejected = df[df['decision'] == 'REJECTED']['utility']
utility_at_home = df[df['decision'] == 'AT-HOME']['utility']

ax3.hist([utility_accepted, utility_rejected, utility_at_home,
          fcfs_accepted_utilities, fcfs_rejected_utilities], bins=50,
         label=['Utility Accepted', 'Utility Rejected', 'Utility At-Home',
                'FCFS Accepted', 'FCFS Rejected'], alpha=0.7)
ax3.set_title('Distribution of Patient Utilities')
ax3.set_xlabel('Utility Value')
ax3.set_ylabel('Frequency')
ax3.legend()

# Plot rejected utility over time for both approaches
ax4.plot(rejected_utility_over_time, label='Utility-based Rejected')
ax4.plot(fcfs_rejected_utility_over_time, label='FCFS Rejected', linestyle='--')
ax4.set_title('Rejected Utility Over Time')
ax4.set_xlabel('Time (minutes)')
ax4.set_ylabel('Total Rejected Utility')
ax4.legend()

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