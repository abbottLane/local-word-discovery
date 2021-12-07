import os
DATA_DIR = "/home/wlane/Desktop/sparse_data_manual_work/allo_transcriptions_sg"

files = os.listdir(DATA_DIR)
lines = []

for file in files:
    if file.endswith('.txt'):
        with open(os.path.join(DATA_DIR, file), "r") as f:
            line = f.read()
            lines.append(line)

lengths = {}
for l in lines:
    l_length = len(l.split())
    if l_length in lengths:
        lengths[l_length] += 1
    else:
        lengths[l_length] = 1

# barchart to show distribution of lengths
import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt


x_data = list(lengths.keys())
y_data = list(lengths.values())
data = zip(y_data, x_data)
data = sorted(data, key=lambda x: x[1])

plt.bar([x[1] for x in data], [x[0] for x in data], align='center', alpha=0.5)
xticlabels = [x[1] for x in data]
plt.xticks(xticlabels)
plt.ylabel('Count')
plt.xlabel('Lengths')
plt.title('Distribution of Breath Group Lengths')
plt.show()