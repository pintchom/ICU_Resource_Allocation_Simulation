import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('patients.csv')
print(df["Total Discharges"])

df['Total Discharges'] = df['Total Discharges'].str.replace(',', '').astype(float)

plt.figure(figsize=(15, 8))
plt.bar(df['Hospital Name'], df['Total Discharges'])

plt.xticks(rotation=90)
plt.xlabel('Hospital Name')
plt.ylabel('Total Discharges')
plt.title('Total Discharges by Hospital')

plt.tight_layout()

plt.show()
