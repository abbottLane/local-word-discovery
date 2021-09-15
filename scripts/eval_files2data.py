import os

ALLO_TRANSCRIPTIONS_DIR = "/home/wlane/Desktop/sparse_data_manual_work/allo_transcriptions_sg"
ORTH_TRANSCRIPTIONS_DIR = '/home/wlane/Desktop/sparse_data_manual_work/orth_transcriptions_sg'
OLD_EVAL_DATA_PATH = 'data/sparse_transcriptions_sg.top20.txt'
TOP_N_SEGMENTS = ['bu', 'ngarri', 'ka', 'n', 'ng', 'kun', 'kabirri', 'yime', 'ba', 'yiman', 'kore', 'balanda', 'mayali', 'man', 'bonj', 'wok', 'om', 're', 'marnbu', 'birri']
DATA_OUT_DIR = "data/"

def main():
    data = {}
    files = [f for f in os.listdir(ALLO_TRANSCRIPTIONS_DIR) if f.endswith('txt')]
    for f in files:
        key = f.rstrip('.wav.allo.txt')
        data[key]={}
        with open(os.path.join(ALLO_TRANSCRIPTIONS_DIR, f), "r") as fh:
            lines = fh.readlines()
            data[key]["allo"] = lines[0].rstrip()
    
    files = [f for f in os.listdir(ORTH_TRANSCRIPTIONS_DIR) if f.endswith('txt')]
    for f in files:
        key = f.rstrip('.txt')
        with open(os.path.join(ORTH_TRANSCRIPTIONS_DIR, f), "r") as fh:
            lines = fh.readlines()
            data[key]['orth'] = lines[0].rstrip()
    
    with open(OLD_EVAL_DATA_PATH, "r") as fh:
        doc_txt = fh.read()
        docs = doc_txt.split('\n\n')
        lines = [x.split('\n')[0].split() for x in docs]
        transcriptions = [x.split('\n')[1] for x in docs]

        segments = []
        for l in lines:
            line_keepers = []
            for gr in l:
                if len(gr) > 1:
                    line_keepers.append(gr)
            segments.append(line_keepers)
        
        for doc_id, ddict in data.items():
            for i, tr in enumerate(transcriptions):
                if ddict['orth'] == tr:
                    ddict['segments'] = segments[i]

        

    with open(os.path.join(DATA_OUT_DIR, "word_discovery_data.txt"), "w") as f:
        i = 0
        for doc_id, ddict in data.items():
            f.write(ddict['allo'] + "\n")
            f.write(ddict['orth'] + "\n")
            if 'segments' in ddict:
                f.write(' '.join(ddict['segments']) + "\n\n")
            else:
                f.write('NONE' + '\n\n')
            i+=1



if __name__== "__main__":
    main()
