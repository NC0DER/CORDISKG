import os

# Path variables.
base_path = r'C:\Users\Nick\Desktop\CORDIS'
input_path = os.path.join(base_path, 'Calls 2021')
output_path = os.path.join(base_path, 'output.xlsx')
aux_keys_path = os.path.join(base_path, 'keyphrases.txt')
projects_csv = os.path.join(base_path, 'cordis-h2020projects.csv')
deliverables_csv = os.path.join(base_path, 'cordis-h2020projectDeliverables.csv')
deliverables_dir = os.path.join(base_path, 'deliverables')
persons_csv = os.path.join(base_path, 'persons.csv')
project_keyphrases_csv = os.path.join(base_path, 'project_keyphrases.csv')
deliverables_keyphrases_csv = os.path.join(base_path, 'deliverables_keyphrases.csv')

# Session variables
debug = True
extract_data = False
create = False
run_algorithms = True

# Database variables
uri = 'bolt://localhost:7687'
user = 'neo4j'
pwd = '123'

# Algorithmic variables
top_n = 10
ngram_range = (1, 3)
cutoff = 0.7
