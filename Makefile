analyzer:
	hfst-xfst -e "source grammars/kunwok.foma" -e "save stack grammars/kunwok.hfst"

tests:
	python align_predict.py -l wam -p ŋawokdibriwambunngangangume -g grammars/kunwok.hfst
	python align_predict.py -l wok birriwam -p ŋawokdibriwambunngangangume -g grammars/kunwok.hfst
	