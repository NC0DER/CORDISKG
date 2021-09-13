import os
import pandas
from CordisKG.utils import counter, load_models, clear_screen, postprocess

@counter
def extract_persons_to_csv(deliverables_dir, persons_csv):
    nlp_model = load_models()[0]
    rows = []
    
    # Change current working directory to the deliverables directory.
    os.chdir(deliverables_dir)

    # Find document filenames and paths.
    docnames = sorted(os.listdir())
    docpaths = list(map(os.path.abspath, docnames))

    total = len(docnames)
    for i, (docname, docpath) in enumerate(zip(docnames, docpaths)):
        print(f'Processing {i} in {total} documents.')

        # Open the file and read the text.
        with open(docpath, 'r', encoding = 'utf-8-sig', errors = 'ignore') as file:
            text = file.read().replace('\n', ' ')

        # Perform NER with spacy.
        doc = nlp_model(text)

        # Extract entities of the text that are classified
        # as persons with full names. 
        persons = list(set(
            x.text for x in doc.ents 
            if x.label_ == 'PERSON' 
            and x.text.count(' ') >= 1
            and not any(char.isdigit() for char in x.text))
        )

        # Postprocessing removes punctuation except '.' 
        # and extra whitespace from each name in the list.
        persons = [x for x in postprocess(persons) if x.strip()]

        # If the persons list is empty, then continue to the next deliverable.
        if not persons: continue

        # Isolate the name of the file, which is the rcn.
        rcn = docname.split('.txt')[0]

        # Each row is a list of rcn and persons 
        # in a ';' separated string.
        rows.append([rcn, ';'.join(persons)])
        clear_screen()

    # Write all rows into a dataframe
    df = pandas.DataFrame(rows, columns = [
        'rcn', 'persons'
    ])

    # Set the index to the first column and save to an csv file.
    df.set_index(['rcn']).to_csv(persons_csv)
    return
