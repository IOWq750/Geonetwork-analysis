import networkx as nx

Ashkatov_vote = ''
Golovnin_vote = 'Razvenkov'
Gorunov_vote = 'Ashkatov'
Korosteleva_vote = 'Kuznechenko'
Kudryavzev_vote = 'Razvenkov'
Kuznechenko_vote = 'Gorunov'
Podlovchenko_vote = 'Korosteleva'
Razvenkov_vote = 'Ashkatov'
Shilyakina_vote = 'Korosteleva'


vote_list = [('Ashkatov', Ashkatov_vote), ('Golovnin', Golovnin_vote), ('Gorunov', Gorunov_vote),
             ('Korosteleva', Korosteleva_vote), ('Kudryavzev', Kudryavzev_vote), ('Kuznechenko', Kuznechenko_vote),
             ('Podlovchenko', Podlovchenko_vote), ('Razvenkov', Razvenkov_vote), ('Shilyakina', Shilyakina_vote)]
G = nx.DiGraph()
G.add_edges_from(vote_list)
pr = nx.pagerank(G)
print(pr)
