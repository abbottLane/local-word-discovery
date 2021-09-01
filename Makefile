analyzer:
	hfst-xfst -e "source grammars/kunwok.foma" -e "save stack grammars/kunwok.hfst"

tests:
	python align_predict.py -l wam -p ŋawokdibriwambunngangangume -g grammars/kunwok.hfst
	python align_predict.py -l wok birriwam -p ŋawokdibriwambunngangangume -g grammars/kunwok.hfst
	python align_predict.py -l kunwok kun -p natkurwɔkkatbɛtɛkunmajaltɛ -g grammars/kunwok.hfst
	python align_predict.py -l bolbme -p jubɔkabiribɔɹbmɛbɔŋkɛnbalantaənbiniɲuɛ -g grammars/kunwok.hfst
	python align_predict.py -l nahne biri -p nanɛbiriamaɳbɔmwurwʈ -g grammars/kunwok.hfst
	python align_predict.py -l kabirri -p kabiribɔʃmɛbuɟtmɛniman -g grammars/kunwok.hfst
	python align_predict.py -l kabirri kabirri bed -p kabiriturkmarɛɲkabiriutuɟmanmɛbɛtbɛrɛ -g grammars/kunwok.hfst
	python align_predict.py -l kun bukkan kabirri -p nimɛkunmajliimanikikamɛtibukanbulantaɛbɛniɲkabirɹɔwɔrɛ -g grammars/kunwok.hfst
	python align_predict.py -l bukbukkan bolkme -p kabɛnbubukanbamanmɛkabirituɟɛŋbɔkabiribɔlkmɛbɔ -g grammars/kunwok.hfst
	