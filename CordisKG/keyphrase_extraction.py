import os
import json
import numpy as np
import pandas as pd
import CordisKG.models
import CordisKG.utils

def keyphrase_extraction(input_path, out_path, top_n):
    # Initialize the spacy and keybert models.
    nlp_model, bert_model = CordisKG.utils.load_models()

    # Initialize the empty document set.
    documents = {}
    language = ''

    # Change current working directory to the dataset directory.
    os.chdir(input_path)

    # Find the language of the current dataset.
    with open(os.path.join(os.getcwd(), 'language.txt'), 
              'r', encoding = 'utf-8-sig', errors = 'ignore') as text:
        language = text.read().rstrip().lower()
        
    # Find document / key filenames and paths.
    # Each time we enter the subdirectory 
    # of the current working directory.
    # First the docs then the keys subdirectory.

    os.chdir(os.path.join(os.getcwd(), 'documents'))
    docnames = sorted(os.listdir())
    docpaths = list(map(os.path.abspath, docnames))

    total = len(docnames)
    for i, (docname, docpath) in enumerate(zip(docnames, docpaths)):
        print(f'Processing {i} in {total} documents.')
        with open(docpath, 'r', encoding = 'utf-8-sig', errors = 'ignore') as file:
            text = file.read().replace('\n', ' ')
            documents[docname] = {
                '1-keybert': CordisKG.models.keybert(text, bert_model, top_n = top_n, measure = 'maxsum', diversity = 0.7),
                '2-textrank': CordisKG.models.textrank(text, nlp_model, top_n = top_n),
                '3-singlerank': CordisKG.models.singlerank(text, top_n = top_n),
                '4-yake': CordisKG.models.yake(text, top_n = top_n, dedupFunc = 'seqm'),
            }
        CordisKG.utils.clear_screen()

    # Write ngrams from each method to a json file.
    with open(out_path, 'w',
        encoding = 'utf-8-sig', errors = 'ignore') as file:
        file.write(json.dumps(documents, indent = 4, separators = (',', ':')))



