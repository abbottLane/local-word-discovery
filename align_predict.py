import hfst
import re
import argparse
from timeit import default_timer as timer

def load_file_lines(filepath):
    lines = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
    return [x.rstrip() for x in lines]

MULTI_CHAR_GRAPHEMES = load_file_lines('resources/multichar_graphemes.txt')
PHONE2ORTH_RULES = load_file_lines('resources/phone_to_orth.txt')
LOCAL_LEXICON = set(load_file_lines('resources/local_wordlist.txt'))
GLOBAL_LEXICON = sorted([x.split() for x in load_file_lines('resources/global_wordlist.txt')], key=lambda x: x[0])

def predict(phone_str, lexemes, grammar):
    if len(lexemes) == 0: 
        return []

    # Filter Global Lexicon to only those entries which are anchored; makes network compilation tractable.
    contains_lexeme_pattern = re.compile('\w*' + '|'.join(lexemes) + '\w*')
    filtered_global_lexicon = list([w for w in GLOBAL_LEXICON if re.findall(contains_lexeme_pattern, w[0])])
    filtered_10 = [x[0] for x in sorted(filtered_global_lexicon, key = lambda x: int(x[1]), reverse=True)[:int(len(filtered_global_lexicon)* .1)]]
    filtered_20 = [x[0] for x in sorted(filtered_global_lexicon, key = lambda x: int(x[1]), reverse=True)[:int(len(filtered_global_lexicon)* .2)]]
    filtered_30 = [x[0] for x in sorted(filtered_global_lexicon, key = lambda x: int(x[1]), reverse=True)[:int(len(filtered_global_lexicon)* .3)]]

    
    tokd_lexemes = tokenize_lexemes(lexemes)

    stream = hfst.HfstInputStream(grammar)
    analyzer_fst = None
    if not stream.is_eof():
        analyzer_fst = stream.read()
    analyzer_fst.output_project()
    analyzer_fst.eliminate_flags()

    # turn phone_str and lexemes into FST strs
    phone_str_fst = hfst.regex('[ ' + ' '.join([x for x in phone_str]) + ' ]')
    lexemes_fst = hfst.regex('[ X ' + ' X '.join(tokd_lexemes.split('  ')) + ' X ]')

    # Build Lexeme transducer: Lexemes are represented as an FST which allows any char between lexemes in order
    # define LexemePattern [[LEXEMES .o. [X -> ?*]].i].u;
    lexemes_fst.compose(hfst.regex('[X -> ?*]'))
    lexemes_fst.invert()
    lexemes_fst.input_project()
    lexeme_pattern = lexemes_fst

    # Define useful edit distance FSTs
    # define Edit1 [?* [?:0|0:?] ?*]^<2;
    # define Edit2 [?* [?:0|0:?] ?*]^<3;
    edit1 = hfst.regex('[?* [?:0|0:?] ?*]^<2')
    edit2 = hfst.regex('[?* [?:0|0:?] ?*]^<3')


    ######################
    ##   GENERATION     ##
    ######################

    # Turn phone stream into FSA of all possible orthographic realizations
    # define OrthStrs  [phone_str_fst  .o. NoisyPhones];
    noisy_phones = hfst.regex(' .o. '.join(PHONE2ORTH_RULES))
    phone_str_fst.compose(noisy_phones)
    orthstrs = phone_str_fst

    #####################################
    ##     ALIGNMENT CONSTRAINTS       ##
    ##################################### 
    # define Edit0Align [[?]* LexemePattern [?]*]["^"]*; 
    # define Edit1Align [[?]* [ Edit1 .o. LexemePattern] [?]*][0:"^"];
    # define Edit2Align [[?]* [ Edit2 .o. LexemePattern] [?]*][0:"^"][0:"^"];
    # ........... (dynamically allocated depending on number of known segments. 2 edit distance per segment > 3 chars, else 1)
    # define EditN Align .....
    # define AlignedOrth [OrthStrs .o. [ Edit0Align | Edit1Align | Edit2Align ]];
    
    alignment_edit_max = sum([2 if len(x) >=3 else 1 for x in lexemes])
    editN_align = []
    for i in range(alignment_edit_max): # Dynamically allocate edit distance allowance depending on number of known lexemes
        edit_i_align = hfst.regex('[?]*')
        if i == 0:
            edit_i_align.concatenate(lexeme_pattern)
            edit_i_align.concatenate(hfst.regex('[?]*'))
            edit_i_align.concatenate(hfst.regex('["^"]*'))
        else: 
            edit_i = hfst.regex('[?* [?:0|0:?] ?*]^<' + str(i +1))
            edit_i.compose(lexeme_pattern)
            edit_i_align.concatenate(edit1)
            edit_i_align.concatenate(hfst.regex('[?]*'))
            edit_i_align.concatenate(hfst.regex('["^"]*'))
            edit_mark_str = '[0:"|"]'
            edit_i_align.concatenate(hfst.regex(edit_mark_str*i))
        editN_align.append(edit_i_align)


    aligned_edits = editN_align[0]
    for edit_align_pattern in editN_align:
        aligned_edits.disjunct(edit_align_pattern)
    
    aligned_orth = orthstrs
    aligned_orth.compose(aligned_edits)
    
    ###################################
    # WORD DISCOVERY CONSTRAINTS     ##
    ###################################
    # define Edit0Discover [[?:0]* LEXICON [?:0]*]["^"]*;
    # define Edit1Discover [[?:0]* [Edit1 .o. LEXICON] [?:0]*][0:"^"];
    # define Edit2Discover [[?:0]* [Edit2 .o. LEXICON] [?:0]*][0:"^"][0:"^"];
    # define DiscoverWords [AlignedOrth .o. [ Edit0Discover | Edit1Discover | Edit2Discover]];
    
    edit0discover = hfst.regex('[?:0]*')
    edit0discover.concatenate(analyzer_fst)
    edit0discover.concatenate(hfst.regex('[?:0]*'))
    edit0discover.concatenate(hfst.regex('["|"]*["^"]*'))

    edit1discover = hfst.regex('[?:0]*')
    edit1.compose(analyzer_fst)
    edit1discover.concatenate(edit1)
    edit1discover.concatenate(hfst.regex('[?:0]*'))
    edit1discover.concatenate(hfst.regex('["|"]*["^"]*'))
    edit1discover.concatenate(hfst.regex('[0:"^"]'))

    edit2discover = hfst.regex('[?:0]*')
    edit2.compose(analyzer_fst)
    edit2discover.concatenate(edit2)
    edit2discover.concatenate(hfst.regex('[?:0]*'))
    edit2discover.concatenate(hfst.regex('["|"]*["^"]*'))
    edit2discover.concatenate(hfst.regex('[0:"^"][0:"^"]'))
 
    edit0discover.disjunct(edit1discover)
    edit0discover.disjunct(edit2discover)
    
    aligned_orth.compose(edit0discover)
    discover_words = aligned_orth

    # results = discover_words.extract_paths(max_cycles=1, max_number=400, output='dict')

    # deduped_results = set()
    # for inp, outlist in results.items():
    #     for out in outlist:
    #         deduped_results.add(re.sub('@_EPSILON_SYMBOL_@', '', str(out[0])))
    
    # print(list(deduped_results))
    # print('########################################################')

    ################################################
    # FILTER                                     ##
    ################################################
    ### 1: Results should be anchored at a known lexeme (Anchored)
    # define AnchoredWords [?* LEXEMESB ?*];
    anchored = hfst.regex('[?* [' + ' | '.join(list(set(tokd_lexemes.split('  ')))) + '] ?*]')
    
    ### 2: Results are found in the local lexicon (Topical)
    topical = hfst.regex('[' + ' | '.join(tokenize_lexemes(LOCAL_LEXICON).split('  ')) + ' ["^"]*]')
    
    # ### 3: Results are found in the Global Lexicon (10% Attested)
    attested_10 = hfst.regex('[' + ' | '.join(tokenize_lexemes(list(filtered_10)).split('  ')) + ' ["^"]*]')

    # ### 4: Results are found in the Global Lexicon (20% Attested)
    attested_20 = hfst.regex('[' + ' | '.join(tokenize_lexemes(list(filtered_20)).split('  ')) + ' ["^"]*]')

    # ### 5: Results are found in the Global Lexicon (30% Attested)
    attested_30 = hfst.regex('[' + ' | '.join(tokenize_lexemes(list(filtered_30)).split('  ')) + ' ["^"]*]')

    ### 4: Results are a minimum edit distance (Phonotactically Plausible)
    edit1filter = hfst.regex('[[?-"^"]* ["^"]^<2 ]')
    edit2filter = hfst.regex('[[?-"^"]* ["^"]^<3 ]')
    edit3filter = hfst.regex('[[?-"^"]* ["^"]^<4 ]')
    
    
    
    # Lenient composition filters
    discover_words.lenient_composition(anchored)
    discover_words.lenient_composition(attested_20)
    discover_words.lenient_composition(attested_10)
    discover_words.lenient_composition(topical) 
    discover_words.lenient_composition(edit2filter)
    discover_words.lenient_composition(edit1filter)


    discover_words.minimize()
    discover_words.determinize()
    
    results = discover_words.extract_paths(max_cycles=1, output='dict')

    deduped_results = set()
    for inp, outlist in results.items():
        for out in outlist:
            deduped_results.add(re.sub('@_EPSILON_SYMBOL_@', '', str(out[0])))
    
    final_results = list(deduped_results)
    print(final_results)
    return final_results

def tokenize_lexemes(lexemes):
    matches = re.findall('|'.join(MULTI_CHAR_GRAPHEMES) + "|.", " ".join(lexemes))
    return ' '.join([x.lstrip() for x in matches])


if __name__== "__main__":
    parser = argparse.ArgumentParser(description="FST-based Local Word Discovery")
    parser.add_argument('-l', '--lexemes', nargs='+', type=str)
    parser.add_argument('-p', '--phones', type=str)
    parser.add_argument('-g', '--grammar', type=str)
    parser.add_argument('-i', '--interactive', action="store_true")

    args = parser.parse_args()

    if not args.phones:
        print("#### INTERACTIVE MODE ####")

        DATA ='data/word_discovery_data.txt'
        with open(DATA, "r") as f:
            lines = f.readlines()

        for idx in range(0, len(lines), 4):
            phones =   lines[idx].rstrip()
            orthography = lines[idx+1].rstrip()
            lexemes = []
            print(phones)
            inp = input('Give lexemes in order:')
            lexemes = inp.rstrip().split()
            predict(phones, lexemes, 'grammars/kunwok.hfst')
    else:
        predict(args.phones, args.lexemes, args.grammar)


    # test_phones = 'kumɛkɛbɛnkarkambɛŋaribɔmubuŋŋɔnɲamɛɛkaburkmaŋatbɛrɛkuku'
    # test_lexemes = ["ngarri"]#["ka", "ka", "ngarri", "ng", "ng", "ka", "ng", "ng"]
    # test_grammar = 'grammars/kunwok.hfst'
    # start = timer()
    # predict(test_phones, test_lexemes, test_grammar)
    # end = timer()
    # time_taken = end-start
    # print("Time: " + str(time_taken))