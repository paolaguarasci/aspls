% =============================================================================
% test.lp — catalog of asp_core2.lark constructs (Clingo-safe, SATISFIABLE)
% Run: clingo examples/test.lp 0
% =============================================================================

% --- comments ---------------------------------------------------------------
% line comment to end of line

% --- #const -----------------------------------------------------------------
#const n = 3.
#const width = 2.

% --- facts: nullary, compound, int (pos/neg), identifiers, ranges -----------
ok.
ready.
node(a).
node(b).
node(c).
edge(a, b).
edge(b, c).
value(1).
value(2).
value(-1).
weight(a, 1).
weight(b, 2).
weight(c, 3).
bird(tweety).
penguin(pingu).
bird(pingu).
candidate(1).
candidate(2).
candidate(3).
size(n).
label(hello).
domain(1..n).
domain(1..width).

% --- disjunctive fact -------------------------------------------------------
maybe_a ; maybe_b.

% --- head disjunction over a domain -----------------------------------------
chosen(X) ; rejected(X) :- candidate(X).

% --- rules: positive body, negation -----------------------------------------
flies(X) :- bird(X), not penguin(X).
alarm :- ok, ready.

% --- terms / ranges bound by domain vars ------------------------------------
cell(X) :- size(N), X = 1..N.
pair(A, B) :- A = 1..width, B = 1..width.

% --- comparisons: all COMPARE_OP (term vs term) -----------------------------
eq(X)  :- candidate(X), X = 1.
neq(X) :- candidate(X), X != 1.
lt(X)  :- candidate(X), X < 3.
le(X)  :- candidate(X), X <= 2.
gt(X)  :- candidate(X), X > 1.
ge(X)  :- candidate(X), X >= 2.
same(X, Y)    :- candidate(X), candidate(Y), X = Y.
ordered(X, Y) :- candidate(X), candidate(Y), X < Y.

% --- aggregates: #count #sum #max #min --------------------------------------
num_nodes(N) :- N = #count{ X : node(X) }.
total(S)     :- S = #sum{ W,X : weight(X, W) }.
peak(M)      :- M = #max{ V : value(V) }.
floor(M)     :- M = #min{ V : value(V) }.

% aggregate COMPARE_OP term  /  term COMPARE_OP aggregate
has_nodes :- #count{ X : node(X) } > 0.
bounded   :- 1 <= #count{ X : node(X) }.
enough    :- #count{ X : chosen(X) } >= 1.

% multiple aggregate elements separated by ';'
mixed(C) :- C = #count{ X : node(X); Y : edge(Y, _) }.

% bind two aggregates then compare (aggregate = aggregate is invalid in Clingo)
exact :- N = #count{ X : chosen(X) }, M = #count{ X : candidate(X) }, N <= M.

% --- constraints ------------------------------------------------------------
:- chosen(X), rejected(X).
:- #count{ X : chosen(X) } < 1.
:- not ok.

% --- mixed body: literal, not, comparison, aggregate ------------------------
valid(X) :-
    candidate(X),
    not rejected(X),
    X >= 1,
    X <= n,
    #count{ Y : edge(X, Y) } >= 0.

% --- #minimize { weight@prio, terms... : body ; ... } -----------------------
#minimize { W@2, X : chosen(X), weight(X, W) }.
#minimize { 1@1, X : rejected(X) }.

% --- #show ------------------------------------------------------------------
#show flies/1.
#show chosen/1.
#show num_nodes/1.
#show total/1.
#show peak/1.
#show floor/1.
#show mixed/1.
#show valid/1.
#show maybe_a/0.
#show maybe_b/0.
#show alarm/0.
#show exact/0.
#show enough/0.
#show has_nodes/0.
#show cell/1.
#show pair/2.
