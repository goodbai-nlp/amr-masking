import re
import json
import glob
import yaml
import copy
import random
import penman as pm
from tqdm import tqdm
from pathlib import Path
from typing import List, Union, Iterable
from treelib import Node, Tree
from converter import penman2tree, tree2penman
from masker import mask_node
from penman_interface import load as pm_load


def _tokenize_encoded_graph(encoded):
    linearized = re.sub(r"(\".+?\")", r" \1 ", encoded)
    pieces = []
    for piece in linearized.split():
        if piece.startswith('"') and piece.endswith('"'):
            pieces.append(piece)
        else:
            piece = piece.replace("(", " ( ")
            piece = piece.replace(")", " ) ")
            piece = piece.replace(":", " :")
            piece = piece.replace("/", " / ")
            piece = piece.replace(":<mask>", "<mask>")
            piece = piece.strip()
            pieces.append(piece)
    linearized = re.sub(r"\s+", " ", " ".join(pieces)).strip()
    return linearized.split(" ")


def dfs_linearize(graph):
    graph_ = copy.deepcopy(graph)
    graph_.metadata = {}
    linearized = pm.encode(graph_)
    linearized_nodes = _tokenize_encoded_graph(linearized)

    if use_pointer_tokens:
        remap = {}
        for i in range(1, len(linearized_nodes)):
            nxt = linearized_nodes[i]
            lst = linearized_nodes[i - 1]
            if nxt == "/":
                remap[lst] = f"<pointer:{len(remap)}>"
        i = 1
        linearized_nodes_ = [linearized_nodes[0]]
        while i < (len(linearized_nodes)):
            nxt = linearized_nodes[i]
            lst = linearized_nodes_[-1]
            if nxt in remap:
                if lst == "(" and linearized_nodes[i + 1] == "/":
                    nxt = remap[nxt]
                    i += 1
                elif lst.startswith(":"):
                    nxt = remap[nxt]
            linearized_nodes_.append(nxt)
            i += 1
        linearized_nodes = linearized_nodes_
        if remove_pars:
            linearized_nodes = [n for n in linearized_nodes if n != "("]
    return linearized_nodes


def read_raw_amr_data(
    paths: List[Union[str, Path]], use_recategorization=False, dereify=True, remove_wiki=False,
):
    """ code for loading AMR from a set of files
        - use_recategorization: use graph recategorization trick
        - dereify: Dereify edges in g that have reifications in model.
        - remove_wiki: remove wiki links
    """
    assert paths
    if not isinstance(paths, Iterable):
        paths = [paths]

    graphs = []
    for path_ in paths:
        for path in glob.glob(str(path_)):
            path = Path(path)
            graphs.extend(pm_load(path, dereify=dereify, remove_wiki=remove_wiki))

    assert graphs

    if use_recategorization:
        for g in graphs:
            metadata = g.metadata
            metadata["snt_orig"] = metadata["snt"]
            tokens = eval(metadata["tokens"])
            metadata["snt"] = " ".join(
                [
                    t
                    for t in tokens
                    if not ((t.startswith("-L") or t.startswith("-R")) and t.endswith("-"))
                ]
            )

    return graphs


if __name__ == "__main__":
    random.seed(42)
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(
        description="AMR processing script",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--config', type=Path, default='default.yaml',
        help='Use the following config for hparams.')
    parser.add_argument('--mask_method', type=str, choices=['node', 'subtree'], help='The masking method. (random/subtree)')
    parser.add_argument('--pct', type=int, default=0, help='Percentage of masking nodes. (int)')
    parser.add_argument('--input_file', type=str,
        help='The input AMR file.')
    parser.add_argument('--output_prefix', type=str,
        help='The output_prefix.')
    
    args, unknown = parser.parse_known_args()

    with args.config.open() as y:
        config = yaml.load(y, Loader=yaml.FullLoader)

    remove_pars = False
    use_pointer_tokens = False
    graphs = read_raw_amr_data(
        [args.input_file],
        use_recategorization=config["use_recategorization"],
        remove_wiki=config["remove_wiki"],
        dereify=config["dereify"],
    )

    line_amr, sentences, mask_line_amr = [], [], []

    for g in tqdm(graphs):
        lin_tokens = dfs_linearize(g)
        sentences.append(g.metadata["snt"])
        #line_amr.append(" ".join(lin_tokens[1:-1]))
        line_amr.append(" ".join(lin_tokens))
        ### masking ###
        t = pm.configure(g)
        amr_tree, amr_vars = penman2tree(t)
        if args.mask_method == "node":
            mask_node(amr_tree, amr_vars, float(args.pct/100))
        mask_pm_tree = tree2penman(amr_tree)
        mask_pm_graph = pm.interpret(mask_pm_tree)
        mask_lin_tokens = dfs_linearize(mask_pm_graph)
        mask_line_amr.append(" ".join(mask_lin_tokens))

    print(f"all {len(line_amr)} AMRs processed")

    with open(args.output_prefix + ".amr", "w", encoding="utf-8") as fout:
        fout.write("\n".join(line_amr) + "\n")

    with open(args.output_prefix + ".txt", "w", encoding="utf-8") as fout:
        fout.write("\n".join(sentences) + "\n")

    with open(args.output_prefix + ".maskamr", "w", encoding="utf-8") as fout:
        fout.write("\n".join(mask_line_amr) + "\n")
    
    res_out = [json.dumps({"sent": sent, "amr": lamr, "mask_amr": msklmar}) for lamr, sent, msklmar in zip(line_amr, sentences, mask_line_amr)]

    with open(args.output_prefix + ".jsonl", "w", encoding="utf-8") as fout:
        fout.write("\n".join(res_out) + "\n")

