"""Author: Xinglong Bai"""
"""This is an application which takes an gene name and an drug name as input, and return several
diseases which related to the gene and drug, then visualized in graph form"""

"================ build User Interface and Input =============="
import sys
if sys.version_info[0] < 3:
    from Tkinter import *
else:
    from tkinter import *

from elasticsearch import Elasticsearch

import networkx as nx
import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt 
from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# the pyplot Figure object, which will be embeded to tkinter.canvas later
f = plt.figure()
a = f.add_subplot(111)
plt.axis('off')

# create tkinter graphic UI
top = Tk()
top.title("Literature Based Discovery SemMed")
frame = Frame(top)
frame.pack()

middleframe = Frame(top)
middleframe.pack(side = TOP)

bottomframe = Frame(top)
bottomframe.pack(side = TOP)

l1 = Label(frame, text = "Drug")
l1.pack(side = LEFT)
w1 = Entry(frame, bd = 3)
w1.pack(side = LEFT)
l2 = Label(frame, text = "Gene")
l2.pack(side = LEFT)
w2 = Entry(frame, bd = 3)
w2.pack(side = LEFT)

l3 = Label(middleframe, text = "Gene")
l3.pack(side = LEFT)
w3 = Entry(middleframe, bd = 3)
w3.pack(side = LEFT)
l4 = Label(middleframe, text = "Disease")
l4.pack(side = LEFT)
w4 = Entry(middleframe, bd = 3)
w4.pack(side = LEFT)

l5 = Label(bottomframe, text = "Drug")
l5.pack(side = LEFT)
w5 = Entry(bottomframe, bd = 3)
w5.pack(side = LEFT)
l6 = Label(bottomframe, text = "Disease")
l6.pack(side = LEFT)
w6 = Entry(bottomframe, bd = 3)
w6.pack(side = LEFT)
canvas_exist = False


"=================function for query in elasticsearch==========="
def make_query(es, name, grammar_name, semtype, grammar_type, grammar_result):
    ## in predication_aggregate use sql query to find relation between drug and disease
    ## e.g. select * from PREDICATION_AGGREGATE where s_type='clnd' and o_type='dsyn' limit *;
    ## relation: (clnd->dsyn<->gngm)
    target = es.search(index = "semantic_medline", doc_type = "predication_aggregate", body = { 
                    "query" : { 
                        "bool" : {
                                "must" : [
                                        {"match" : {grammar_name : name}},
                                        {"match" : {grammar_type : semtype}}
                                    ]
                            }
                        }
                    }, size = 100, _source_include = [grammar_result, "predicate"], request_timeout=30.0)
    return target


"================ query search from elasticsearch ============="
def main(search):
    ##Stimulant Rheumatoid vasculitis
    print("search is " + search)
    es = Elasticsearch()
    
    drug = "" ## SEMTYPE=phsu/clnd
    gene = "" ## SEMTYPE = gngm  e.g ABCD1 AAMP NAT1  TYPE=ENTREZ, GHR!=NULL e.g ABCA1 
    disease = "" ## SEMTYPE=dsyn
    
    if search == "drug_gene":        
        drug = w1.get()
        gene = w2.get()
    elif search == "gene_disease":
        gene = w3.get()
        disease = w4.get()
    else:
        drug = w5.get()
        disease = w6.get()

    if search == "drug_gene":
        toDrug = make_query(es, drug, "s_name", "dsyn", "o_type", "o_name")
        toGeneS = make_query(es, gene, "s_name", "dsyn", "o_type", "o_name")
        toGeneO = make_query(es, gene, "o_name", "dsyn", "s_type", "s_name")
    elif search == "gene_disease":
        toGeneS = make_query(es, gene, "s_name", "phsu", "o_type", "o_name")
        toGeneO = make_query(es, gene, "o_name", "phsu", "s_type", "s_name")
        toDisease = make_query(es, disease, "o_name", "phsu", "s_type", "s_name")
    else:
        toDrugS = make_query(es, drug, "s_name", "gngm", "o_type", "o_name")
        toDrugO = make_query(es, drug, "o_name", "gngm", "s_type", "s_name")
        toDiseaseS = make_query(es, disease, "s_name", "gngm", "o_type", "o_name")
        toDiseaseO = make_query(es, disease, "o_name", "gngm", "s_type", "s_name")
        
    #initialize dict to represent vertices adjacency  left: first input  right: second input
    if search == "drug_gene":
        left = drug
        right = gene
    elif search == "gene_disease":
        left = gene
        right = disease
    else:
        left = drug
        right = disease
        
    Drug_Disease_Gene = dict()
    Drug_Disease_Gene[right] = dict()
    Drug_Disease_Gene[left] = dict()

    share = dict()
    share[right] = dict()
    share[left] = dict()

    relations = dict()

    if search == "drug_gene":
        for i in toGeneS['hits']['hits']:
            Drug_Disease_Gene[right][i['_source']['o_name']] = i['_source']['predicate']

        for i in toGeneO['hits']['hits']:
            Drug_Disease_Gene[right][i['_source']['s_name']] = i['_source']['predicate']

        for i in toDrug['hits']['hits']:
            Drug_Disease_Gene[left][i['_source']['o_name']] = i['_source']['predicate']
    elif search == "gene_disease":
        for i in toGeneS['hits']['hits']:
            Drug_Disease_Gene[left][i['_source']['o_name']] = i['_source']['predicate']

        for i in toGeneO['hits']['hits']:
            Drug_Disease_Gene[left][i['_source']['s_name']] = i['_source']['predicate']
        
        for i in toDisease['hits']['hits']:
            Drug_Disease_Gene[right][i['_source']['s_name']] = i['_source']['predicate']
    else:
        for i in toDrugS['hits']['hits']:
            Drug_Disease_Gene[left][i['_source']['o_name']] = i['_source']['predicate']
        for i in toDrugO['hits']['hits']:
            Drug_Disease_Gene[left][i['_source']['s_name']] = i['_source']['predicate']
        for i in toDiseaseS['hits']['hits']:
            Drug_Disease_Gene[right][i['_source']['o_name']] = i['_source']['predicate']
        for i in toDiseaseO['hits']['hits']:
            Drug_Disease_Gene[right][i['_source']['s_name']] = i['_source']['predicate']

        

    ## get the predicates and shared concepts
    for k in Drug_Disease_Gene[right].keys():
        if k in Drug_Disease_Gene[left]:
            share[right][k] = {'weight' : 1}
            share[left][k] = {'weight' : 1}

            relations[(right, k)] = Drug_Disease_Gene[right][k]
            relations[(left, k)] = Drug_Disease_Gene[left][k]
            
    "=========================plot graph=========================="

 

    #network x create graph
    #retrieval node labels
    G = nx.from_dict_of_dicts(share)
    labels = G.nodes()

    #retrieval predicates from semantic medline as edge labels
    edge_labels = dict()
    Edges = G.edges()
    for e in Edges:
        if (e[0], e[1]) in relations.keys():
            edge_labels[e] = relations[(e[0], e[1])]
        elif (e[1], e[0]) in relations.keys():
            edge_labels[e] = relations[(e[1], e[0])]

    # draw graph
    colors = []
    for n in labels:
        if n == gene:
            colors.append("yellow")
        elif n == drug:
            colors.append("greenyellow")
        elif n == disease:
            colors.append("aqua")
        else:
            if search == "drug_gene":
                colors.append("aqua")
            elif search == "gene_disease":
                colors.append("greenyellow")
            else:
                colors.append("yellow")

    label = zip(G.nodes(), G.nodes())

    pos = nx.shell_layout(G)
    nx.draw_networkx(G, pos, node_color = colors, node_size=400)
    nx.draw_networkx_labels(G, pos, labels = dict(label), font_size = 3)
    nx.draw_networkx_edge_labels(G, pos, edge_labels = edge_labels)

    # plot graph on UI canvas
    global canvas_exist
    
    if not canvas_exist:
        global xlim
        global ylim
        global canvas
        xlim=a.get_xlim()
        ylim=a.get_ylim()
        canvas = FigureCanvasTkAgg(f, master=top)
        canvas.show()
        canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=1)
        canvas_exist = True
    else:
        a.cla()
        nx.draw_networkx(G, pos, node_color = colors, node_size=400)
        nx.draw_networkx_labels(G, pos, labels = dict(label), font_size = 3)
        nx.draw_networkx_edge_labels(G, pos, edge_labels = edge_labels)
        a.set_xlim(xlim)
        a.set_ylim(ylim)
        plt.axis('off')
        canvas.draw()

"========================complete user interface====================="

searchButton = Button(frame, text = "search", command = lambda: main("drug_gene"))
searchButton.pack(side = RIGHT)

searchButton = Button(middleframe, text = "search", command = lambda: main("gene_disease"))
searchButton.pack(side = RIGHT)

searchButton = Button(bottomframe, text = "search", command = lambda: main("drug_disease"))
searchButton.pack(side = RIGHT)

top.mainloop()
print("the end")
