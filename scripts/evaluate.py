from timeit import default_timer as timer
import subprocess
import os
import ast
import re
import json

def load_known_vocab(filepath):
    with open(filepath, "r") as f:
        lines = [x.split('\t')[0] for x in f.readlines()]
        return set(lines)

INPUT_DATA = "data/word_discovery_data.txt"
OUTPUT_DATA = "data/word_discovery_data.out.txt"
KNOWN_VOCAB = load_known_vocab('data/sg_vocab.20.txt')

def main():
    # Read in data
    data = load_data(INPUT_DATA)

    # calculate baseline transcription density
    data = calc_density(data, mode="baseline")

    sorted_data = sorted(list(data.values()), key=lambda x: len(x['phones']))
    data = dict(zip(data.keys(), sorted_data))
    # invoke 1 iteration of discovery
    suggested_words = discover(data)

    # calculate new transcription density
    data = calc_density(data, mode="discovered")

    with open("annotated.json", "w") as f :
        json.dump(data,f)
    # calculate relative density increase
    # data = calc_density(data, mode="discovered")

    # visualize data? bar plot x is docN, y is relative density increase

def load_data(filepath):
    ddict = {}
    with open(filepath, "r") as f:
        doc_txt = f.read()
        lines = doc_txt.split("\n\n")
        for i, line in enumerate(lines):
            phones, orth, knowns = line.split('\n')
            
            docid = "doc" + str(i)
            ddict[docid] = {}
            ddict[docid]["phones"] = phones
            ddict[docid]["orth"] = orth
            ddict[docid]["knowns"] = knowns
    return ddict


def calc_density(ddata, mode):
    if mode == "baseline":
        for doc_id, data in ddata.items():
            gold_orth = data['orth']
            present_lexemes =data['knowns']
            
            transcribed_length = sum([len(x) for x in present_lexemes.split() if x != "NONE"])
            total_transcription_length = sum([len(x) for x in gold_orth.split()])
            density = float(transcribed_length)/total_transcription_length
            ddata[doc_id]["baseline"] = density
    if mode == "discovered":
        for doc_id, data in ddata.items():
            gold_orth = data['orth']
            present_lexemes =data['knowns']

            transcribed = set()
            for pred in data['predictions']:
                pred = re.sub("\^+", "", pred)
                for o in data['orth'].split():
                    if pred == o:
                        transcribed.add(pred)
                        
            transcribed_length = sum([len(x) for x in list(transcribed)])
            for known in data['knowns'].split():
                found = False
                for tr in list(transcribed):
                    if known in tr:
                        found=True
                if not found:
                    transcribed_length += len(known)

            total_transcription_length = sum([len(x) for x in gold_orth.split()])
            density = float(transcribed_length)/total_transcription_length
            ddata[doc_id]["predicted_density"] = density

    return ddata    

def discover(ddata):
    for doc_id, data in ddata.items():
        phone_str = ''.join(data['phones'].split())
        gold_orth = data['orth']
        present_lexemes =data['knowns'].split()

        if data['knowns'][0] == "NONE":
            data['knowns'] = []  

        start = timer()
        # results = predict(phone_str=phone_str, lexemes=present_lexemes, grammar='grammars/kunwok.hfst')
        print(os.getcwd())
        command = ["python", "./align_predict.py", "-l"]
        command.extend(present_lexemes)
        command.extend( ["-p", phone_str, "-g",  "grammars/kunwok.hfst"])
        results = subprocess.run(command, capture_output=True) # -l, -p, -g : lexemes, phones, grammar
        end = timer()
        time_taken = end-start

        result_list = ast.literal_eval(results.stdout.decode('utf-8'))
        print(phone_str)
        print(result_list)
        print(doc_id + " time taken: " + str(time_taken))

        ddata[doc_id]['predictions'] = result_list

    return ddata

def get_present_lexemes(sparse_line):
    tokens = sparse_line.split()
    return [x for x in tokens if x in set(KNOWN_VOCAB)]

if __name__ == "__main__":
    
    main()