from CordisKG.export_keys import export_keys_to_csv
from CordisKG.extract_persons import extract_persons_to_csv
from CordisKG.config import *
from neo4j import ServiceUnavailable
from CordisKG.neo4j_wrapper import Neo4jDatabase
from CordisKG.create import *
from CordisKG.parse_pdfs import export_pdfs_to_txt

def CORDISKG():
    # Open the database.
    try:
        database = Neo4jDatabase(uri, user, pwd)
        # Neo4j server is unavailable.
        # This client app cannot open a connection.
    except ServiceUnavailable as error:
        print('\t* Neo4j database is unavailable.')
        print('\t* Please check the database connection before running this app.')
        input('\t* Press any key to exit the app...')
        sys.exit(1)

    if extract_data:
        export_keys_to_csv(
           projects_csv, project_keyphrases_csv, 
           aux_keys_path, top_n, ngram_range, cutoff,
           id_field = 'id', text_field = 'objective'
        )
        export_keys_to_csv(
            deliverables_csv, deliverables_keyphrases_csv, 
            aux_keys_path, top_n, ngram_range, cutoff, 
            id_field = 'rcn', text_field = 'description'
        )
        export_pdfs_to_txt(deliverables_csv, deliverables_dir)
        extract_persons_to_csv(deliverables_dir, persons_csv)

    if create:
        create_unique_constraints(database)
        create_project_graph(database, projects_csv)
        create_keyphrases_graph(database, project_keyphrases_csv, 'Project')
        create_deliverable_graph(database, deliverables_csv, persons_csv)
        create_keyphrases_graph(database, deliverables_keyphrases_csv, 'Deliverable')

    if run_algorithms:
        create_similarity_graph(database, False, True)
        run_initial_algorithms(database)

if __name__  ==  '__main__': CORDISKG()
