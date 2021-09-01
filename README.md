# local-word-discovery
Finite state method for expanding partial annotations into full words, conditioned on a phone stream.

Prereqs:
- Python >=3.7
- `hfst` python package installed in your local env

Usage:
- The command line tool can be invoked as follows: `python align_predict.py -l wam -p ŋawokdibriwambunngangangume -g grammars/kunwok.hfst`
    - -l, --lexemes: a list of lexemes that are known to occur in the audio/phone stream, in order 
    - -p, --phones: the phone sequence which contains words we want to discover
    - -g, --grammar: the compiled HFST grammar whose lower side contains the vocabulary of morphotactically valid words in the language


- Additionally, the constraint-based approach employed here leverages two wordlists:
    - resources/local_wordlist.txt: contains a list of words relevant to the current project or document. Discovered words which are also found to be locally relevant have precedence over other discovered words.
    - resources/global_wordlist.txt: contains a list of words attested in the language. This can be a txt file dump of some large corpus. The purpose of this is to prioritize words which are attested in the language, above those which may only be theoretically morphotactically valid.

- Finally, the FST requires some basic knowledge about the language we are working with.
    - resources/multichar_graphemes.txt: provides a list of multicharacter graphemes in your language. This allows the FST to segment orthography properly so that graphemes can be mapped to phones.
    - phone_to_orth.txt: a canonical mapping of phones to graphemes. One-to-many mappings are allowed here, but not strictly necessary.