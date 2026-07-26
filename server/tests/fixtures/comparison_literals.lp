cell(X, Y) :- size(N), X=1..N, Y=1..N, not forbidden(X, Y).
numero_celle(X) :- X = #count{ A,B : cell(A,B) }.
big :- N = #count{X : item(X)}, N > 5.
