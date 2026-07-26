% =============================================================================
% ASP grammar tour — esercita ogni costrutto riconosciuto da asp_core2.lark
% =============================================================================

% --- commenti (COMMENT: % fino a fine riga) ---------------------------------
% questa riga e' interamente un commento

% --- direttive --------------------------------------------------------------
#const n = 5.
#const width = 10.

#show chosen/1.
#show edge/2.

#minimize { cost(X) @ 2, penalty }.
#minimize { soft(X) }.

% --- fatti: atomi nullary / compound, range nei termini ---------------------
ok.
node(a).
node(b).
edge(a, b).
value(1).
value(-3).
domain(1..n).
domain(1..10).
label(hello).

% --- fatto disgiuntivo (head = disjunction) ---------------------------------
maybe_a ; maybe_b.

% --- regole: head :- body. --------------------------------------------------
% literal positivo, negazione (not), piu' letterali nel body
flies(X) :- bird(X), not penguin(X).

% atomo nullary in testa e nel body
alarm :- danger, not silenced.

% disgiunzione in testa
chosen(X) ; rejected(X) :- candidate(X).

% --- termini: VARIABLE, IDENTIFIER, INT, range ------------------------------
% range_bound: INT | IDENTIFIER | VARIABLE
cell(X) :- size(N), X = 1..N.
cell(Y) :- Y = 1..width.
pair(A, B) :- A = 1..3, B = 2..4.

% --- confronti (comparison + tutti i COMPARE_OP) ----------------------------
% operandi: term | aggregate
eq(X)    :- X = 0.
neq(X)   :- X != 0.
lt(X)    :- X < 10.
le(X)    :- X <= 10.
gt(X)    :- X > 0.
ge(X)    :- X >= 0.

% confronto tra termini
same(X, Y) :- X = Y.
ordered(X, Y) :- X < Y.

% --- aggregati: #count #sum #max #min ---------------------------------------
% aggregate_elem con term_tuple : body
num_nodes(N) :- N = #count{ X : node(X) }.
total(S)     :- S = #sum{ W,X : weight(X, W) }.
peak(M)      :- M = #max{ V : value(V) }.
floor(M)     :- M = #min{ V : value(V) }.

% aggregate_elem solo body (senza tupla a sinistra di :)
has_any :- #count{ node(X) } > 0.

% piu' elementi nell'aggregato (separati da virgola)
mixed(C) :- C = #count{ X : node(X), Y : edge(Y, _) }.

% aggregato come operando sinistro/destro di un confronto
enough :- #count{ X : chosen(X) } >= 2.
bounded :- 1 <= #count{ X : chosen(X) }.
exact :- #count{ X : chosen(X) } = #count{ X : candidate(X) }.

% --- vincoli (constraint: :- body.) -----------------------------------------
:- chosen(X), rejected(X).
:- #count{ X : chosen(X) } < 1.
:- not ok.

% --- rule body misto: literal, not, comparison, aggregate -------------------
valid(X) :-
    candidate(X),
    not forbidden(X),
    X >= 1,
    X <= n,
    #count{ Y : edge(X, Y) } > 0.
