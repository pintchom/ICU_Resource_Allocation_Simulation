import numpy as np
import matplotlib.pyplot as plt

# Distribution data where:
# Rows are urgency levels (urgent, semi-urgent, non-urgent)
# Columns are age groups (0-17, 18-44, 45-74, 65+)
distribution_data = {
    'urgent': [0.19, 0.403, 0.219, 0.188],
    'semi_urgent': [0.283, 0.446, 0.175, 0.096], 
    'non_urgent': [0.277, 0.469, 0.173, 0.081]
}

# Calculate overall probabilities for each urgency level
overall_probs = {
    'urgent': 0.612,
    'semi_urgent': 0.287,
    'non_urgent': 0.101
}

# Create two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10,12))

# First subplot - Age distribution by urgency
age_groups = ['0-17', '18-44', '45-64', '65+']
x = np.arange(len(age_groups))
width = 0.25

rects1 = ax1.bar(x - width, distribution_data['urgent'], width, label='Urgent')
rects2 = ax1.bar(x, distribution_data['semi_urgent'], width, label='Semi-Urgent')
rects3 = ax1.bar(x + width, distribution_data['non_urgent'], width, label='Non-Urgent')

ax1.set_ylabel('Probability')
ax1.set_title('Age Distribution by Urgency Level')
ax1.set_xticks(x)
ax1.set_xticklabels(age_groups)
ax1.legend()

# Second subplot - Overall urgency distribution
urgency_levels = list(overall_probs.keys())
probabilities = list(overall_probs.values())
x_points = np.arange(len(urgency_levels))

ax2.bar(x_points, probabilities)
ax2.set_xticks(x_points)
ax2.set_xticklabels(urgency_levels)
ax2.set_ylabel('Probability')
ax2.set_title('Overall Distribution of Urgency Levels')

plt.tight_layout()
plt.show()
