import traceback

class GraphAlgos:
    """
    Wrapper class which handle the graph algorithms 
    more efficiently, by abstracting repeating code.
    """
    database = None # Static variable shared across objects.

    def __init__(self, database, node_list, rel_list, orientation = "NATURAL"):
        # Initialize the static variable and class member.
        if GraphAlgos.database is None:
            GraphAlgos.database = database

        # Construct the relationship string.
        if type(rel_list[0]) is str:
            rel_string = ', '.join(
                (f'{rel}: {{type: "{rel}", orientation: "{orientation}"}}')
                for rel in rel_list)
        else:
            rel_string = ', '.join(
                (f'{rel[0]}: {{type: "{rel[0]}", orientation: "{rel[1]}", properties: {rel[2]}}}')
                for rel in rel_list)

        # Assign the graph details in the self object.
        self.node_list = node_list
        self.rel_list = rel_list
        self.orientation = orientation

        # Construct the projection of the anonymous graph.
        self.graph_projection = (
            f'{{nodeProjection: {node_list}, '
            f'relationshipProjection: {{{rel_string}}}'
        )

    def pagerank(self, write_property, max_iterations = 20, damping_factor = 0.85):
        setup = (
            f'{self.graph_projection}, '
            f'writeProperty: "{write_property}", '
            f'maxIterations: {max_iterations}, '
            f'dampingFactor: {damping_factor}}}'
        )
        GraphAlgos.database.execute(f'CALL gds.pageRank.write({setup})', 'w')

    def nodeSimilarity(self, write_property, write_relationship, cutoff = 0.5, top_k = 10):
        setup = (
            f'{self.graph_projection}, '
            f'writeProperty: "{write_property}", '
            f'writeRelationshipType: "{write_relationship}", '
            f'similarityCutoff: {cutoff}, '
            f'topK: {top_k}}}'
        )
        query = f'CALL gds.nodeSimilarity.write({setup})'
        GraphAlgos.database.execute(f'CALL gds.nodeSimilarity.write({setup})', 'w')

    def louvain(self, write_property, max_levels = 10, max_iterations = 10):
        setup = (
            f'{self.graph_projection}, '
            f'writeProperty: "{write_property}", '
            f'maxLevels: {max_levels}, '
            f'maxIterations: {max_iterations}}}'
        )
        GraphAlgos.database.execute(f'CALL gds.louvain.write({setup})', 'w')

    def create_named_graph(self, named_graph):
        # Construct the node string.
        node_string = ', '.join(f'"{node}"' for node in self.node_list)

        # Construct the relationship string.
        if type(self.rel_list[0]) is str:
            rel_string = ', '.join(
                (f'{rel}: {{orientation: "{self.orientation}"}}')
                for rel in self.rel_list)
        else:
            rel_string = ', '.join(
                (f'{rel[0]}: {{orientation: "{rel[1]}", properties: {rel[2]}}}')
                for rel in self.rel_list)
        rel_string = '{' + rel_string + '}'

        query = (
            f'CALL gds.graph.create("{named_graph}", {node_string}, {rel_string})'
        )
        print(query)
        GraphAlgos.database.execute(query, 'w')
        

    def train_test_split_rels(self, named_graph, relationship, remaining_type, holdout_type, holdout_percent = 0.2):
        setup = (
            f'"{named_graph}", {{'
            f'relationshipTypes: ["{relationship}"], '
            f'remainingRelationshipType: "{relationship}_{remaining_type}", '
            f'holdoutRelationshipType: "{relationship}_{holdout_type}", '
            f'holdoutFraction: {holdout_percent}}}'
        )
        query = f'CALL gds.alpha.ml.splitRelationships.mutate({setup})'
        print(query)
        GraphAlgos.database.execute(query, 'w')

    def link_prediction(self, named_graph, train_rel, test_rel, model_name, train_mode):
        """
        This function retrieves the existing relationships of the subgraph
        (positive examples), and calculates the non-existing ones (negative
        examples), as to measure the class ratio (negative / positive).
        Then trains a link prediction model based on the class ratio,
        and supplied parameters.
        """
        # Get nodes and relationship count of the subgraph.
        rel_string = '|'.join(self.rel_list)
        query = f'MATCH (n:{self.node_list[0]})-[r:{rel_string}]->() RETURN COUNT(n), COUNT(r)'
        result = GraphAlgos.database.execute(query, 'r')
        node_count, existing_rels = result[0][0], result[0][1]
        
        all_possible_rels = node_count * (node_count - 1) / 2 # n(n - 1) / 2
        non_existing_rels = all_possible_rels - existing_rels
        class_ratio = non_existing_rels / existing_rels
        
        query = (
            f'CALL gds.alpha.ml.linkPrediction.train("{named_graph}", {{ '
            f'trainRelationshipType: "{train_rel}", '
            f'testRelationshipType: "{test_rel}", '
            f'modelName: "{model_name}", '
            f'featureProperties: [], '
            f'validationFolds: 5, '
            f'classRatio: {class_ratio}, '
            f'randomSeed: 2, '
            f'params: [ '
            f'{{penalty: 0.5, maxIterations: 1000}}, '
            f'{{penalty: 1.0, maxIterations: 1000}}, '
            f'{{penalty: 0.0, maxIterations: 1000}} '
            f']}}) YIELD modelInfo RETURN '
            f'modelInfo.bestParameters AS winningModel, '
            f'modelInfo.metrics.AUCPR.outerTrain AS trainGraphScore, '
            f'modelInfo.metrics.AUCPR.test AS testGraphScore'
        )
        print(query)
        result = GraphAlgos.database.execute(query, 'w')
        print(result)




    # These methods enable the use of this class in a with statement.
    def __enter__(self):
        return self

    # Automatic cleanup of the created graph of this class.
    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)