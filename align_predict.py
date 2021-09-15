import hfst
import re
import argparse
from libhfst import HfstBasicTransducer, HfstTransducer

def load_file_lines(filepath):
    lines = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
    return [x.rstrip() for x in lines]

MULTI_CHAR_GRAPHEMES = load_file_lines('resources/multichar_graphemes.txt')
PHONE2ORTH_RULES = load_file_lines('resources/phone_to_orth.txt')
LOCAL_LEXICON = set(load_file_lines('resources/local_wordlist.txt'))
GLOBAL_LEXICON = [x.split()[0] for x in load_file_lines('resources/global_wordlist.txt')]

def main(phone_str, lexemes, grammar):
    # Filter Global Lexicon to only those entries which are anchored; makes network compilation tractable.
    contains_lexeme_pattern = re.compile('\w*' + '|'.join([x for x in lexemes]) + '\w*')
    filtered_global_lexicon = [w for w in GLOBAL_LEXICON if re.findall(contains_lexeme_pattern, w)]
    
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
    # print("LEXEMES_WORDS: " + '[ X ' + ' X '.join(tokd_lexemes.split('  ')) + ' X ]')

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
    # define AlignedOrth [OrthStrs .o. [ Edit0Align | Edit1Align | Edit2Align ]];
    edit0_align = hfst.regex('[?]*')
    edit0_align.concatenate(lexeme_pattern)
    edit0_align.concatenate(hfst.regex('[?]*'))
    edit0_align.concatenate(hfst.regex('["^"]*'))

    edit1_align = hfst.regex('[?]*')
    edit1.compose(lexeme_pattern)
    edit1_align.concatenate(edit1)
    edit1_align.concatenate(hfst.regex('[?]*'))
    edit1_align.concatenate(hfst.regex('["^"]*'))
    edit1_align.concatenate(hfst.regex('[0:"^"]'))

    edit2_align = hfst.regex('[?]*')
    edit2.compose(lexeme_pattern)
    edit2_align.concatenate(edit2)
    edit2_align.concatenate(hfst.regex('[?]*'))
    edit2_align.concatenate(hfst.regex('["^"]*'))
    edit2_align.concatenate(hfst.regex('[0:"^"][0:"^"]'))

    aligned_edits = edit0_align
    aligned_edits.disjunct(edit1_align)
    aligned_edits.disjunct(edit2_align)
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
    edit0discover.concatenate(hfst.regex('["^"]*'))

    edit1discover = hfst.regex('[?:0]*')
    edit1.compose(analyzer_fst)
    edit1discover.concatenate(edit1)
    edit1discover.concatenate(hfst.regex('[?:0]*'))
    edit1discover.concatenate(hfst.regex('["^"]*'))
    edit1discover.concatenate(hfst.regex('[0:"^"]'))

    edit2discover = hfst.regex('[?:0]*')
    edit2.compose(analyzer_fst)
    edit2discover.concatenate(edit2)
    edit2discover.concatenate(hfst.regex('[?:0]*'))
    edit2discover.concatenate(hfst.regex('["^"]*'))
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
    
    ### 3: Results are found in the Global Lexicon (Attested)
    attested = hfst.regex('[' + ' | '.join(tokenize_lexemes(list(filtered_global_lexicon)).split('  ')) + ' ["^"]*]')
    
    ### 4: Results are a minimum edit distance (Phonotactically Plausible)
    edit1filter = hfst.regex('[[?-"^"]* ["^":0]^<2 ]')
    edit2filter = hfst.regex('[[?-"^"]* ["^":0]^<3 ]')
    edit3filter = hfst.regex('[[?-"^"]* ["^":0]^<4 ]')
    edit4filter = hfst.regex('[[?-"^"]* ["^":0]^<5 ]')
    
    # Lenient composition filters
    discover_words.lenient_composition(anchored)
    discover_words.lenient_composition(attested)
    discover_words.lenient_composition(topical) 
    discover_words.lenient_composition(edit1filter) 
    discover_words.lenient_composition(edit2filter)
    discover_words.lenient_composition(edit3filter)
    discover_words.lenient_composition(edit4filter)

    discover_words.minimize()
    discover_words.determinize()
    
    results = discover_words.extract_paths(max_cycles=1, output='dict')

    deduped_results = set()
    for inp, outlist in results.items():
        for out in outlist:
            deduped_results.add(re.sub('@_EPSILON_SYMBOL_@', '', str(out[0])))
    
    print(list(deduped_results))
    
def tokenize_lexemes(lexemes):
    matches = re.findall('|'.join(MULTI_CHAR_GRAPHEMES) + "|.", " ".join(lexemes))
    return ' '.join([x.lstrip() for x in matches])


if __name__== "__main__":
    parser = argparse.ArgumentParser(description="FST-based Local Word Discovery")
    parser.add_argument('-l', '--lexemes', nargs='+', type=str)
    parser.add_argument('-p', '--phones', type=str)
    parser.add_argument('-g', '--grammar', type=str)
    args = parser.parse_args()
    main(args.phones, args.lexemes, args.grammar)

    # test_phones = 'kbiriturkmarɛɲkabiriutuɟmanmɛbɛtbɛrɛ'
    # test_lexemes = ['kabirri', 'kabirri', 'bed']
    # test_grammar = 'grammars/kunwok.hfst'
    #main(test_phones, test_lexemes, test_grammar)
