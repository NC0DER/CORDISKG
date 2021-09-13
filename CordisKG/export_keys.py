import pandas
import CordisKG.models
import CordisKG.utils

def export_keys_to_csv(input_csv, output_csv, aux_keys_path, top_n, ngram_range, cutoff, id_field, text_field):
    """
    Function that reads an input csv, and produces an output csv,
    which has a column with extracted keyphrases from the text.
    """
    # Initialize the spacy and keybert models.
    nlp_model, bert_model = CordisKG.utils.load_models()

    # Clear the screen after loading the models
    CordisKG.utils.clear_screen()

    # Read the input_csv
    rows = pandas.read_csv(input_csv, sep = ';')
    total = len(rows)
    data = []

    # Read all auxiliary keyphrases
    with open(aux_keys_path, 'r', encoding = 'utf-8-sig', errors = 'ignore') as keys:
        aux_keys = keys.read().splitlines()

    for i in range(total):
        print(f'Processing {i} in {total} documents.')

        # Read the text from row.
        text = str(rows[text_field].iloc[i]).replace('\n', ' ')

        # Find if any of the auxiliary keys is present in the text.
        found_aux_keys = CordisKG.utils.find_keys_in_text(text, aux_keys)

        # Extract keyphrases from the text using the selected methods.
        #CordisKG.models.keybert(text, bert_model, ngram_range, top_n = top_n, measure = 'maxsum', diversity = 0.7),
        extracted_keys = [
            CordisKG.models.textrank(text, nlp_model, top_n = top_n), 
            CordisKG.models.singlerank(text, top_n = top_n),
            CordisKG.models.yake(text, ngram_range, top_n = top_n, dedupFunc = 'seqm')
        ]

        # Flatten the list of extracted keyphrases into a single list of all keyphrases
        # and remove common strings from this list.
        all_extracted_keys = (
        CordisKG.utils.remove_common_strings_from_list (
            CordisKG.utils.flatten_list(extracted_keys),
            cutoff
        ))

        # Enhance the list of extracted keys, with the found auxiliary keys.
        all_extracted_keys += found_aux_keys
        keyphrase_string = ';'.join(all_extracted_keys)

        # Format all keyphrases to be newline separated strings.
        data.append([
            rows[id_field].iloc[i],
            f'{keyphrase_string}'
        ])
        CordisKG.utils.clear_screen()
        #break # Debug line
    
    # Construct the dataframe.
    df = pandas.DataFrame(data, columns = [
        id_field, 'keyphrases'
    ])

    # Set the index to the first column and save to a csv file.
    df.set_index([id_field]).to_csv(output_csv)
    return
