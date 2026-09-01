#external a.
#external query(T) : step(T).
#external hold(X, Y) : step(X), edge(X, Y).

step(1).
step(2).
edge(1, 2).

hold(X, Y) :- step(X), edge(X, Y), query(X).
