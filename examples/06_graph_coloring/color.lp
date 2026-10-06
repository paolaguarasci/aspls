% =============================================================================
% Tutorial 6 — Graph coloring (classic modeling lab)
%
% Run:  clingo examples/06_graph_coloring/color.lp 0
% Goal: assign one of three colors so adjacent nodes differ.
%
% Potassco Guide §5.1 n-Coloring. See readme.md learning path and
% Cookbook *Graph 3-coloring*.
% =============================================================================

edge(1, 2). edge(2, 3). edge(3, 1). edge(1, 4). edge(4, 5).

% Treat edges as undirected.
edge(X, Y) :- edge(Y, X).

node(X) :- edge(X, _).
node(X) :- edge(_, X).

color(red).
color(green).
color(blue).

% Guess: each node gets exactly one color.
1 { colored(N, C) : color(C) } 1 :- node(N).

% Check: adjacent nodes must not share a color.
:- edge(X, Y), colored(X, C), colored(Y, C).

#show colored/2.
