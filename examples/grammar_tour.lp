% =============================================================================
% ASP grammar tour — every construct recognized by asp_core2.lark
% Note: some rules intentionally use free variables (e.g. eq(X) :- X = 0).
% Clingo reports those as "unsafe"; add domain facts (bird/1, candidate/1, …)
% for a runnable program.
% =============================================================================

% --- comments (COMMENT: % to end of line) ------------------------------------
% this line is entirely a comment

% --- directives -------------------------------------------------------------
#const n = 5.
#const width = 10.

#show chosen/1.
#show edge/2.

#minimize { 2@2, X : cost(X) }.
#minimize { 1, X : soft(X) }.

% --- facts: nullary / compound atoms, ranges in terms -----------------------
ok.
node(a).
node(b).
edge(a, b).
value(1).
value(-3).
domain(1..n).
domain(1..10).
label(hello).

% --- disjunctive fact (head = disjunction) ----------------------------------
maybe_a ; maybe_b.

% --- rules: head :- body. ---------------------------------------------------
% positive literal, negation (not), multiple body literals
flies(X) :- bird(X), not penguin(X).

% nullary atom in head and body
alarm :- danger, not silenced.

% head disjunction
chosen(X) ; rejected(X) :- candidate(X).

% --- terms: VARIABLE, IDENTIFIER, INT, range --------------------------------
% range_bound: INT | IDENTIFIER | VARIABLE
cell(X) :- size(N), X = 1..N.
cell(Y) :- Y = 1..width.
pair(A, B) :- A = 1..3, B = 2..4.

% --- comparisons (comparison + all COMPARE_OP) ------------------------------
% operands: term | aggregate
eq(X)    :- X = 0.
neq(X)   :- X != 0.
lt(X)    :- X < 10.
le(X)    :- X <= 10.
gt(X)    :- X > 0.
ge(X)    :- X >= 0.

% term vs term
same(X, Y) :- X = Y.
ordered(X, Y) :- X < Y.

% --- aggregates: #count #sum #max #min --------------------------------------
% aggregate_elem with term_tuple : body
num_nodes(N) :- N = #count{ X : node(X) }.
total(S)     :- S = #sum{ W,X : weight(X, W) }.
peak(M)      :- M = #max{ V : value(V) }.
floor(M)     :- M = #min{ V : value(V) }.

% aggregate_elem body only (no tuple left of :) — X must be bound
has_any :- #count{ X : node(X) } > 0.

% multiple aggregate elements (separated by ';' in Clingo, not ',')
mixed(C) :- C = #count{ X : node(X); Y : edge(Y, _) }.

% aggregate as comparison operand (not aggregate = aggregate)
enough :- #count{ X : chosen(X) } >= 2.
bounded :- 1 <= #count{ X : chosen(X) }.
exact :- N = #count{ X : chosen(X) }, M = #count{ X : candidate(X) }, N = M.

% --- constraints (constraint: :- body.) -------------------------------------
:- chosen(X), rejected(X).
:- #count{ X : chosen(X) } < 1.
:- not ok.

% --- choice rules -----------------------------------------------------------
% unbounded / bounded; elements: literal or literal : body; ';' separators
candidate(1).
candidate(2).
1 { chosen(X) : candidate(X) } 1.
{ a; b }.
{ selected(X) : candidate(X) }.
1 { picked(X) : candidate(X) } 1 :- ok.

% --- mixed rule body: literal, not, comparison, aggregate -------------------
valid(X) :-
    candidate(X),
    not forbidden(X),
    X >= 1,
    X <= n,
    #count{ Y : edge(X, Y) } > 0.

% --- weak constraints -------------------------------------------------------
:~ chosen(X). [1@1, X]
:~ a. [2]
