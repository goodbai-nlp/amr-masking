import penman as pm
from treelib import Node, Tree
from converter import penman2tree, tree2penman
from random import sample


def get_maskable_nodes(amr_tree, amr_vars):
    unmaskable_tags = amr_vars.union({'-', '/'})
    maskable_nodes = list(amr_tree.filter_nodes(lambda n: False if n.tag in unmaskable_tags else True))
    return maskable_nodes


def mask_node(amr_tree: Tree, amr_vars: set, prop: float) -> Tree:
    maskable_nodes = get_maskable_nodes(amr_tree, amr_vars)
    sample_nodes = sample(maskable_nodes, int(prop*len(maskable_nodes)))
    for node in sample_nodes:
        node.tag = "<mask>"
    return amr_tree
    
