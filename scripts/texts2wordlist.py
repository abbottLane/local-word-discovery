from os import listdir
from os import path
import re

DIR = '/home/wlane/projects/kunwok-texts'
OUTDIR = 'resources/wordlist.txt'

def clean(word):
    word = re.sub('[\.,_—©§†‡!$”“﻿‘’\*\[\]\-#&)(?\':";]',"", word)
    return word

lines = []
for file in listdir(DIR):
    if file.endswith('txt'):
        with open(path.join(DIR, file), "r") as f:
            lines.extend(f.readlines())

final_words = []
for l in lines:
    words = l.split()
    final_words.extend(clean(x.lower()) for x in words)


counts = {}
for word in final_words:
    if word in counts:
        counts[word] += 1
    else:
        counts[word] = 1 

counts = {k: v for k, v in sorted(counts.items(), key=lambda item: item[1])}
with open(OUTDIR, "w") as f:
    for w, c in counts.items():
        if counts[w] > 1:
            f.write(w + "\t" + str(c) + '\n')

