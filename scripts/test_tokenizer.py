import re



def load_file_lines(filepath):
    lines = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
    return [x.rstrip() for x in lines]

MULTI_CHAR_GRAPHEMES = load_file_lines('resources/multichar_graphemes.txt')
print(MULTI_CHAR_GRAPHEMES)
def tokenize_lexemes(lexemes):
    matches = re.findall('|'.join(MULTI_CHAR_GRAPHEMES) + "|.", " ".join(lexemes))
    print(matches)
    return ' '.join(matches)

print(tokenize_lexemes(["ngabolknan", "birri", "mang"]))
