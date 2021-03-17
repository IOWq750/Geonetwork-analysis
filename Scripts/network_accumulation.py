import arcpy
import networkx as nx

arcpy.env.overwriteOutput = True
input_shp = arcpy.GetParameterAsText(0)
field = arcpy.GetParameterAsText(1)
output_workspace = arcpy.GetParameterAsText(2)
G = nx.read_shp(r'{0}'.format(input_shp))
nodes = G.nodes()
edges = G.edges()
total_dict = nx.get_edge_attributes(G, field)
print(total_dict)
for node in nodes:
    ancestors = list(nx.ancestors(G, node))
    sum_weight = 0
    for coords in ancestors:
        for edge in edges:
            if edge[0] == coords:
                sum_weight += float(total_dict[edge])  # sum weight for upslope edges
                print(sum_weight)
    for edge in edges:
        if edge[0] == node:
            self_weight = float(total_dict[edge])  # weight of the edge itself
            accum_edge = {edge: sum_weight + self_weight}
            arcpy.AddMessage(str(edge) + " has accumulated weight of " + str(sum_weight + self_weight))
            nx.set_edge_attributes(G, accum_edge, 'Accum')
nx.write_shp(G, r'{0}'.format(output_workspace))
