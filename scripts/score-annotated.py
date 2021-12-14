import json
import re
import matplotlib.pyplot as plt
import numpy as np

def main():
    data = read_data(dir='annotated.json')
    scores = score_data(data)
    calculate_stats(scores)

    total_predictions = 0
    for k,v in scores.items():
        nump= v['num_predictions'] 
        if not nump:
            nump=0
        total_predictions += nump 
    print("AVG # predictions: ", total_predictions/len(scores))
    write_data(scores, 'scored.json')

    # Plot the document-level data
    x = list(scores.keys())

    y = [scores[k]['num_predictions'] for k,v in scores.items()]
    y= [x if x != None else 0 for x in y ]
    z = [scores[k]['partial_match'] for k,v in scores.items()]
    k = [scores[k]['exact_match'] for k,v in scores.items()]

    subcategorybar(x[99:], [y[99:],z[99:],k[99:]])
    plt.show()

def subcategorybar(X, vals, width=0.9):
    n = len(vals)
    _X = np.arange(len(X))
    for i in range(n):
        plt.bar(_X - width/1. + i/float(n)*width, vals[i], 
                width=width/float(n), align="edge")   
    plt.xticks(_X, X, rotation=45)

def read_data(dir):
    with open(dir, 'r') as f:
        data = json.load(f)
    return data

def score_data(data):
    scores = {}
    for key, value in data.items():
        scores[key] = score_value(value)
    return scores

def get_substrings(prediction_str, known):
    try:
        left, right = prediction_str.split(known)
        rightsubstrs = ["".join(right[0:i]) for i in range(len(right)+1) ]
        leftsubstrs = ["".join(left[-i:]) for i in range(len(left)+1) ]
        return leftsubstrs[1:], rightsubstrs[1:]
    except:
        # print("BAD STRING FOR SPLITTING: ", prediction_str)
        return [], []

def calculate_stats(scores):
    all_partial_counts = 0
    all_full_counts = 0
    all_predictions = 0
    has_useful_prediction=  0
    has_full_prediction = 0
    has_partial_prediction = 0
    for id, counts in scores.items():
        if counts['num_predictions'] is None:
            continue
        if counts['num_predictions'] == 0:
            continue
        else:
            all_partial_counts += counts['partial_match']
            all_full_counts += counts['exact_match']
            all_predictions += counts['num_predictions']
            scores[id]['exact_match_percent'] = 100*counts['exact_match']/counts['num_predictions']
            scores[id]['partial_match_percent'] = 100*counts['partial_match']/counts['num_predictions']

            if counts['exact_match'] > 0 or counts['partial_match'] > 0:
                has_useful_prediction += 1
            if counts['exact_match'] > 0:
                has_full_prediction += 1
            if counts['partial_match'] > 0:
                has_partial_prediction += 1

    print("Number of documents: ", len(scores))
    print("Total full count percentage: ", 100*all_full_counts/all_predictions)
    print("Total partial count percentage: ", 100*all_partial_counts/all_predictions)
    print("Percent of docs with full prediction: ", 100*has_full_prediction/len(scores))
    print("Percent of docs with partial prediction: ", 100*has_partial_prediction/len(scores))

    print("Percent of docs with useful prediction: ", 100*has_useful_prediction/len(scores))

def score_value(value):
    prediction_counts = {'num_predictions': len(value['predictions']), 'exact_match': 0, 'partial_match': 0}
    if value['knowns'] == "NONE":
        prediction_counts['num_predictions'] = None
        return prediction_counts
    else:
        if value['knowns'] == "man":
            pause = 9
        for prediction in value['predictions']:
            prediction_copy = prediction
            for known in value['knowns'].split():
                # prediction_copy = prediction_copy.replace(known, '')
                prediction_copy = re.sub('\|*\^*', "", prediction_copy)
                
                found = False
                for word in value['orth'].split():
                    # first, check if a prediction is an exact match
                    if prediction == word:
                        prediction_counts['exact_match'] += 1
                        found = True
                        break
                    leftsubstrs, rightsubstrs = get_substrings(prediction_copy, known)
                    for sub in rightsubstrs:
                        if known+sub in word and sub != known:
                            prediction_counts['partial_match'] += 1
                            found = True
                            break
                    
                    for sub in leftsubstrs:
                        if sub+known in word and sub != known:
                            prediction_counts['partial_match'] += 1
                            found = True
                            break
                    if found:
                        break
                if found:
                    break

        return prediction_counts


def write_data(data, dir):
    with open(dir, 'w') as f:
        json.dump(data, f)


if __name__ == "__main__":
    main()