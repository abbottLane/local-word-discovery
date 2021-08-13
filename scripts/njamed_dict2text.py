import json

source = '/home/wlane/projects/kunwok-dictionary/app/dictionary/njamed_dictionary.json'

with open(source) as f:
    dict_dict  = json.load(f)

keep_lines = []
for entry in dict_dict:
    keep_lines.append(entry['orth'])
    for example in entry['examples']:
        for lines in example:
            keep_lines.append(lines)

with open('/home/wlane/projects/kunwok-texts/njamed_text.txt', "w") as f:
    for line in keep_lines:
        f.write(line + "\n")