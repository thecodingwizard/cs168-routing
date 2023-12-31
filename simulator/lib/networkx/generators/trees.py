# -*- encoding: utf-8 -*-
#    Copyright (C) 2015-2018 by
#        Jeffrey Finkelstein <jeffrey.finkelstein@gmail.com>
#        NetworkX developers
#    All rights reserved.
#    BSD license.
#
# Authors:      Jeffrey Finkelstein <jeffrey.finkelstein@gmail.com>
"""Functions for generating trees."""
import random
from collections import defaultdict

import networkx as nx
from networkx.utils import generate_unique_node

__all__ = ["prefix_tree", "random_tree"]

#: The nil node, the only leaf node in a prefix tree.
#:
#: Each predecessor of the nil node corresponds to the end of a path
#: used to generate the prefix tree.
NIL = "NIL"


def prefix_tree(paths):
    """Creates a directed prefix tree from the given list of iterables.

    Parameters
    ----------
    paths: iterable of lists
        An iterable over "paths", which are themselves lists of
        nodes. Common prefixes among these paths are converted into
        common initial segments in the generated tree.

        Most commonly, this may be an iterable over lists of integers,
        or an iterable over Python strings.

    Returns
    -------
    DiGraph
        A directed graph representing an arborescence consisting of the
        prefix tree generated by `paths`. Nodes are directed "downward",
        from parent to child. A special "synthetic" root node is added
        to be the parent of the first node in each path. A special
        "synthetic" leaf node, the "nil" node, is added to be the child
        of all nodes representing the last element in a path. (The
        addition of this nil node technically makes this not an
        arborescence but a directed acyclic graph; removing the nil node
        makes it an arborescence.)

        Each node has an attribute 'source' whose value is the original
        element of the path to which this node corresponds. The 'source'
        of the root node is None, and the 'source' of the nil node is
        :data:`.NIL`.

        The root node is the only node of in-degree zero in the graph,
        and the nil node is the only node of out-degree zero.  For
        convenience, the nil node can be accessed via the :data:`.NIL`
        attribute; for example::

            >>> from networkx.generators.trees import NIL
            >>> paths = ['ab', 'abs', 'ad']
            >>> T = nx.prefix_tree(paths)
            >>> T.predecessors(NIL)  # doctest: +SKIP

    Notes
    -----
    The prefix tree is also known as a *trie*.

    Examples
    --------
    Create a prefix tree from a list of strings with some common
    prefixes::

        >>> strings = ['ab', 'abs', 'ad']
        >>> T, root = nx.prefix_tree(strings)

    Continuing the above example, to recover the original paths that
    generated the prefix tree, traverse up the tree from the
    :data:`.NIL` node to the root::

        >>> from networkx.generators.trees import NIL
        >>>
        >>> strings = ['ab', 'abs', 'ad']
        >>> T, root = nx.prefix_tree(strings)
        >>> recovered = []
        >>> for v in T.predecessors(NIL):
        ...     s = ''
        ...     while v != root:
        ...         # Prepend the character `v` to the accumulator `s`.
        ...         s = str(T.node[v]['source']) + s
        ...         # Each non-nil, non-root node has exactly one parent.
        ...         v = next(T.predecessors(v))
        ...     recovered.append(s)
        >>> sorted(recovered)
        ['ab', 'abs', 'ad']

    """

    def _helper(paths, root, B):
        """Recursively create a trie from the given list of paths.

        `paths` is a list of paths, each of which is itself a list of
        nodes, relative to the given `root` (but not including it). This
        list of paths will be interpreted as a tree-like structure, in
        which two paths that share a prefix represent two branches of
        the tree with the same initial segment.

        `root` is the parent of the node at index 0 in each path.

        `B` is the "accumulator", the :class:`networkx.DiGraph`
        representing the branching to which the new nodes and edges will
        be added.

        """
        # Create a mapping from each head node to the list of tail paths
        # remaining beneath that node.
        children = defaultdict(list)
        for path in paths:
            # If the path is the empty list, that represents the empty
            # string, so we add an edge to the NIL node.
            if not path:
                B.add_edge(root, NIL)
                continue
            # TODO In Python 3, this should be `child, *rest = path`.
            child, rest = path[0], path[1:]
            # `child` may exist as the head of more than one path in `paths`.
            children[child].append(rest)
        # Add a node for each child found above and add edges from the
        # root to each child. In this loop, `head` is the child and
        # `tails` is the list of remaining paths under that child.
        for head, tails in children.items():
            # We need to relabel each child with a unique name. To do
            # this we simply change each key in the dictionary to be a
            # (key, uuid) pair.
            new_head = generate_unique_node()
            # Ensure the new child knows the name of the old child so
            # that the user can recover the mapping to the original
            # nodes.
            B.add_node(new_head, source=head)
            B.add_edge(root, new_head)
            _helper(tails, new_head, B)

    # Initialize the prefix tree with a root node and a nil node.
    T = nx.DiGraph()
    root = generate_unique_node()
    T.add_node(root, source=None)
    T.add_node(NIL, source=NIL)
    # Populate the tree.
    _helper(paths, root, T)
    return T, root


# From the Wikipedia article on Prüfer sequences:
#
# > Generating uniformly distributed random Prüfer sequences and
# > converting them into the corresponding trees is a straightforward
# > method of generating uniformly distributed random labelled trees.
#
def random_tree(n, seed=None):
    """Returns a uniformly random tree on `n` nodes.

    Parameters
    ----------
    n : int
        A positive integer representing the number of nodes in the tree.

    seed : int
        A seed for the random number generator.

    Returns
    -------
    NetworkX graph
        A tree, given as an undirected graph, whose nodes are numbers in
        the set {0, …, *n* - 1}.

    Raises
    ------
    NetworkXPointlessConcept
        If `n` is zero (because the null graph is not a tree).

    Notes
    -----
    The current implementation of this function generates a uniformly
    random Prüfer sequence then converts that to a tree via the
    :func:`~networkx.from_prufer_sequence` function. Since there is a
    bijection between Prüfer sequences of length *n* - 2 and trees on
    *n* nodes, the tree is chosen uniformly at random from the set of
    all trees on *n* nodes.

    """
    if n == 0:
        raise nx.NetworkXPointlessConcept("the null graph is not a tree")
    # Cannot create a Prüfer sequence unless `n` is at least two.
    if n == 1:
        return nx.empty_graph(1)
    random.seed(seed)
    sequence = [random.choice(range(n)) for i in range(n - 2)]
    return nx.from_prufer_sequence(sequence)
