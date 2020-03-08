# Rule-Based AMR Parser for Portuguese (RBAMR)

RBAMR is a rule-based AMR parser for the Abstract Meaning Representation of a sentence in 
Portuguese. For more details, see [here](https://sites.icmc.usp.br/taspardo/IBERAMIA2018-AnchietaPardo.pdf)

# Depencencies
- Python 2
- Parser PALAVRAS [http://visl.sdu.dk/constraint_grammar.html](http://visl.sdu.dk/constraint_grammar.html)

- `pip install -r requirements.txt`

- `sh install.sh`

# Parsing
The input data format for parsing should be a raw document with one sentence per line.

`python init.py -f <input_file>`

# Citation
```
@inproceedings{anchietaPardoParser,
	title={A Rule-Based AMR Parser for Portuguese},
	author={Anchi\^{e}ta, Rafael Torres and Pardo, Thiago Alexandre Salgueiro},
	booktitle={Advances in Artificial Intelligence - IBERAMIA 2018},
	pages={341--353},
	editor={Simari, Guillermo R. and Ferm{\'e}, Eduardo and Guti{\'e}rrez Segura, Flabio and Rodr{\'i}guez Melquiades, Jos{\'e} Antonio},
	year={2018}
}
```
