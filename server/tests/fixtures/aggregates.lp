node(a).
node(b).
edge(a, b).
weight(a, 3).
weight(b, 5).
value(1).
value(-3).

num_nodes(N) :- N = #count{ X : node(X) }.
total(S)     :- S = #sum{ W,X : weight(X, W) }.
peak(M)      :- M = #max{ V : value(V) }.
floor(M)     :- M = #min{ V : value(V) }.
has_any      :- #count{ X : node(X) } > 0.
mixed(C)     :- C = #count{ X : node(X); Y : edge(Y, _) }.
