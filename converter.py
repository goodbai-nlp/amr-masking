import penman as pm
import networkx as nx
from treelib import Node, Tree
import uuid


def penman2tree(penman_tree: pm.Tree):
    top, branches = penman_tree.node
    amr_vars = set()
    tree = Tree()
    tree.create_node(top, 'root')
    for (rel, pm_node) in branches:
        if rel == '/': amr_vars.add(top)
        uuid_role = uuid.uuid4()
        uuid_concept = uuid.uuid4()
        if type(pm_node) == str:
            role = tree.create_node(rel, uuid_role, parent='root')
            tree.create_node(pm_node, uuid_concept, parent=role.identifier)
        else:
            role = tree.create_node(rel, uuid_role, parent='root')
            concept = tree.create_node(pm_node[0], uuid_concept, parent=role.identifier)
            # build tree recursively (pm_node is res_pm_node)
            build_recursion(tree, concept, pm_node, amr_vars)
    return tree, amr_vars


def build_recursion(tree: Tree, top_node: Node, res_pm_node:pm.Tree.node, amr_vars: set):
    top, branches = res_pm_node
    top_id = top_node.identifier
    for (rel, pm_node) in branches:
        if rel == '/': amr_vars.add(top)
        uuid_role = uuid.uuid4()
        uuid_concept = uuid.uuid4()
        if type(pm_node) == str:
            role = tree.create_node(rel, uuid_role, parent=top_id)
            tree.create_node(pm_node, uuid_concept, parent=role.identifier)
        else:
            role = tree.create_node(rel, uuid_role, parent=top_id)
            concept = tree.create_node(pm_node[0], uuid_concept, parent=role.identifier)
            build_recursion(tree, concept, pm_node, amr_vars)    
            
            
def deconstruct_recursion(tree: Tree, top_node: Node, branch_dict: dict, node_order: list):
    top_id = top_node.identifier
    node_order.append(top_node)
    children = tree.children(top_id)
    for child in children: 
        chd_id = child.identifier
        chd_tag = child.tag
        gchd = tree.children(chd_id)[0]
        gchd_id = gchd.identifier
        gchd_tag = gchd.tag
        if top_id not in branch_dict:
            branch_dict.update({top_id: []})
        if gchd.is_leaf():
            chd_tuple = (chd_tag, gchd_tag)
            branch_dict[top_id].append(chd_tuple)
        else:
            branch_dict[top_id].append({chd_id: gchd_id})
            deconstruct_recursion(tree, gchd, branch_dict, node_order)
      
            
def tree2penman(amr_tree: Tree, branch_dict: dict = {}, node_order: list = []) -> pm.Tree:
    deconstruct_recursion(amr_tree,amr_tree.get_node(amr_tree.root), branch_dict, node_order)
    for btm_node in reversed(node_order):
        # btm_node = node_order.pop()
        btm_id = btm_node.identifier
        # btm_tag = btm_node.tag
        rels = branch_dict[btm_id]
        intp_rels = []
        for rel in rels:
            if type(rel) == dict:
                role_id = list(rel.keys())[0]
                role_node = amr_tree.get_node(role_id)
                concept_id = list(rel.values())[0]
                concept_node = amr_tree.get_node(concept_id)
                intp_rels.append((role_node.tag, (concept_node.tag, branch_dict[concept_id])))
            else:
                intp_rels.append(rel)
        branch_dict[btm_id] = intp_rels
    pm_node = (amr_tree.get_node('root').tag, branch_dict['root'])
    pm_tree = pm.Tree(pm_node)
    return pm_tree


if __name__ == "__main__":
    # g = pm.decode("(a / alpha :ARG0 (b / beta) :ARG0-of (g / gamma :ARG1 b))")
    # t = pm.parse("(a / alpha :ARG0 (b / beta) :ARG0-of (g / gamma :ARG1 b))")
    # ::id bolt12_10474_1421.6 ::date 2012-12-07T07:50:17 ::annotator SDL-AMR-09 ::preferred
    # t = pm.parse("(o / obvious-01 :ARG1 (a / and :op1 (l / leave-17 :polarity - :ARG1 (o2 / or :op1 (p / problem :topic (s2 / society)) :op2 (p3 / problem :topic (p2 / politics)))) :op2 (l2 / leave-17 :polarity - :ARG1 (s / sequela :ARG0-of (c / cause-01 :ARG1 (h / headache :beneficiary (g / generation :time (a2 / after :op1 t)))))) :time (t / then)))")
    t = pm.parse("(a / and :op1 (d / die-01 :ARG1 (p / person :quant (m / many))) :op2 (d2 / destroy-01 :ARG1 (p2 / property :quant (m2 / much))) :op3 (d3 / disaster :domain (i / it) :mod (g / great) :ARG1-of (c / clear-06 :degree (q / quite))))")
    print(t.node)
    amr_tree, amr_vars = penman2tree(t)
    amr_tree.show()

    # print(amr_vars)
    # print(amr_tree.all_nodes())
    # print([n.tag for n in amr_tree.all_nodes()],'\n')
    
    # unmaskable_tags = amr_vars.union({'-', '/'})
    # maskable_nodes = list(amr_tree.filter_nodes(lambda n: False if n.tag in unmaskable_tags else True))
    # print(maskable_nodes)
    # print([n.tag for n in maskable_nodes])
    # print(amr_tree.to_json(with_data=False))
    # print(amr_tree.children('root'))
    
    # branch_dict = {}
    # node_order = []
    # deconstruct_recursion(amr_tree,amr_tree.get_node(amr_tree.root), branch_dict, node_order)
    # print(branch_dict)
    penman_tree = tree2penman(amr_tree)
    print(penman_tree.node)
    amr_tree1, _= penman2tree(penman_tree)
    amr_tree1.show()