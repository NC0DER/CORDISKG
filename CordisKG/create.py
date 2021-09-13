import pandas
from itertools import product
from CordisKG.utils import counter, clear_screen, tokenize
from CordisKG.graph_algos import *

def create_unique_constraints(database):
    """
    Wrapper function that gathers all CREATE CONSTRAINT queries,
    in one place.
    """
    database.execute('CREATE CONSTRAINT ON (project:Project) '
                     'ASSERT project.id IS UNIQUE', 'w')
    database.execute('CREATE CONSTRAINT ON (deliverable:Deliverable) '
                     'ASSERT deliverable.rcn IS UNIQUE', 'w')
    database.execute('CREATE CONSTRAINT ON (person:Person) '
                     'ASSERT person.name IS UNIQUE', 'w')
    database.execute('CREATE CONSTRAINT ON (organization:Organization) '
                     'ASSERT organization.name IS UNIQUE', 'w')
    database.execute('CREATE CONSTRAINT ON (keyphrase:Keyphrase) '
                     'ASSERT keyphrase.name IS UNIQUE', 'w')
    return

@counter
def create_project_graph(database, cordis_path):
    """
    Function that reads the csv, and creates the knowledge graph.
    """
    rows = pandas.read_csv(cordis_path, sep = ';')
    total = len(rows)
    for i in range(total):

        print(f'Creating {i} out of {total} projects...')
        # Create the project node, with all its fields.
        query = (
            'CREATE (p:Project {'
            f'id: {rows["id"].iloc[i]}, '
            f'acronym: "{rows["acronym"].iloc[i]}", '
            f'call: "{rows["call"].iloc[i]}", '
            f'status: "{rows["status"].iloc[i]}", '
            f'programme: "{rows["programme"].iloc[i]}", '
            f'topics: "{rows["topics"].iloc[i]}", '
            f'startDate: "{rows["startDate"].iloc[i]}", '
            f'endDate: "{rows["endDate"].iloc[i]}", '
            f'projectUrl: "{rows["projectUrl"].iloc[i]}", '
            f'totalCost: {float(str(rows["totalCost"].iloc[i]).replace(",", "."))}, '
            f'ecMaxContribution: {float(str(rows["ecMaxContribution"].iloc[i]).replace(",", "."))}, '
            f'fundingScheme: "{rows["fundingScheme"].iloc[i]}"}})'
        )
        database.execute(query, 'w')
        coordinator = rows["coordinator"].iloc[i]

        # Construct the participants list.
        participants = str(rows["participants"].iloc[i]).split(';')

        # Unwind the list of participants and their relationships with the project.
        # Create the coordinator and its relationship as well.
        query = (
            f'MATCH (p:Project {{id: {rows["id"].iloc[i]}}}) '
            f'UNWIND {participants} as name '
            'MERGE (o:Organization {name: name}) '
            'MERGE (o)-[:participates_in]->(p) '
            f'MERGE (c:Organization {{name: "{coordinator}"}}) '
            'MERGE (c)-[:participates_in]->(p) '
            'MERGE (c)-[:coordinates]->(p) '
        )
        database.execute(query, 'w')
        clear_screen()
    return

def create_keyphrases_graph(database, keys_path, target):
    """
    Function that reads the csv, and creates the keyphrases graph.
    """
    rows = pandas.read_csv(keys_path, sep = ',')
    total = len(rows)

    # Create the id field string
    id_field = 'id' if target == 'Project' else 'rcn'

    for i in range(total):
        print(f'Creating keyphrases for {i} out of {total} {target}s...')

        # Construct the keyphrases list.
        keys = str(rows["keyphrases"].iloc[i]).split(';')

        # Unwind the list of keyphrases and their relationships with the target.
        query = (
            f'MATCH (t:{target} {{{id_field}: {rows[{id_field}].iloc[i, 0]}}}) '
            f'UNWIND {keys} as key '
            'MERGE (k:Keyphrase {name: key}) '
            'MERGE (t)-[:includes]->(k) '
        )
        database.execute(query, 'w')
        clear_screen()
    return

@counter
def create_deliverable_graph(database, deliverables_csv, persons_csv):
    """
    Function that reads the csvs, and creates the deliverables graph.
    """
    rows = pandas.read_csv(persons_csv, sep = ',')
    other_rows = pandas.read_csv(deliverables_csv, sep = ';')
    rows = rows.sort_values('rcn')
    other_rows = other_rows.sort_values('rcn')

    total = len(rows)
    j = 0
    for i in range(total):
        print(f'Creating deliverable {i} out of {total} deliverables...')

        # In case of a missing record, skip the index.
        while rows["rcn"].iloc[i] != other_rows["rcn"].iloc[j]:
            j += 1

        # Construct the persons list.
        persons = str(rows["persons"].iloc[i]).split(';')

        # Unwind the list of keyphrases and their relationships with the project.
        query = (
            f'MATCH (p:Project {{id: {other_rows["projectID"].iloc[i]}}}) '
            f'UNWIND {persons} as person '
            f'MERGE (d:Deliverable {{ '
            f'rcn: {rows["rcn"].iloc[i]}, '
            f'title: "{other_rows["title"].iloc[i]}", '
            f'projectAcronym: "{other_rows["projectAcronym"].iloc[i]}", '
            f'programme: "{other_rows["programme"].iloc[i]}", '
            f'deliverableType: "{other_rows["deliverableType"].iloc[i]}", '
            f'url: "{other_rows["url"].iloc[i]}"}}) '
            'MERGE (a:Person {name: person}) '
            'MERGE (d)-[:belongs]->(p) '
            'MERGE (a)-[:writes]->(d) '
        )
        database.execute(query, 'w')
        clear_screen()
    return


@counter
def create_similarity_graph(database, 
                            similar_organizations_projects = True,
                            similar_persons = True
                           ):
    """
    Function that creates a similarity graph between organizations,
    based on the keyphrases of their common projects.
    """
    # Remove similarity edges from previous iterations.
    database.execute('MATCH ()-[r:is_similar]->() DELETE r', 'w')

    # Create the similarity graph using Jaccard similarity measure.
    if similar_organizations_projects:
        with GraphAlgos(database, 
                       ['Organization', 'Project', 'Keyphrase'],
                       [('participates_in', 'NATURAL', []), 
                       ('includes', 'NATURAL', [])]) as graph1:
            graph1.nodeSimilarity(
                write_property = 'score', 
                write_relationship = 'is_similar', 
                cutoff = 0.23, top_k = 1
            )
    if similar_persons:
        with GraphAlgos(database, 
                       ['Person', 'Deliverable', 'Project', 'Keyphrase'],
                       [('writes', 'NATURAL', []), 
                       ('belongs', 'NATURAL', []),
                       ('includes', 'NATURAL', [])]) as graph2:
            graph2.nodeSimilarity(
                write_property = 'score', 
                write_relationship = 'is_similar', 
                cutoff = 0.23, top_k = 1
            )
    return


def run_initial_algorithms(database):
    """
    Function that runs centrality & community detection algorithms,
    in order to prepare the data for analysis and visualization.
    Pagerank & Louvain are used, respectively.
    """
    with GraphAlgos(database, ['Project', 'Keyphrase'], 
                    ['includes'], orientation = 'UNDIRECTED') as graph1:
        graph1.pagerank(write_property = 'pagerank')

    with GraphAlgos(database, ['Project'], ['is_similar']) as graph2:
        graph2.louvain(write_property = 'community')

    with GraphAlgos(database, ['Organization'], ['is_similar']) as graph3:
        graph3.louvain(write_property = 'community')

    with GraphAlgos(database, ['Deliverable'], ['is_similar']) as graph4:
        graph4.louvain(write_property = 'community')

    with GraphAlgos(database, ['Person'], ['is_similar']) as graph5:
        graph5.louvain(write_property = 'community')

    return


def link_prediction_ml(database, train_mode = True):
    """
    Function which creates the train, test subgraph and runs the link
    prediction algorithm.
    """
    with GraphAlgos(database, ['Person'], ['is_similar'], orientation = 'UNDIRECTED') as graph:
        # The link prediction ml model requires a named graph.
        #graph.create_named_graph('graph')
        # Create test graph and train graph respectively.
        #graph.train_test_split_rels('graph', 'is_similar', 'remaining', 'test')
        #graph.train_test_split_rels('graph', 'is_similar_remaining', 'ignored', 'train', 1.0)
        graph.link_prediction('graph', 'is_similar_remaining_train', 'is_similar_test', 'LP', train_mode)
        