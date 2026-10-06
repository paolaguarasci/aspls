% =============================================================================
% Tutorial 5 — Weak constraints (soft preferences)
%
% Run:  clingo examples/05_weak_constraint/soft_menu.lp 0
% Goal: each guest picks a dish; prefer cheap dishes via :~ (soft).
%
% Compare with Tutorial 2 (hard choice) and Tutorial 3 (#minimize).
% Potassco Guide: Language §3.1 weak constraints. See readme.md learning path.
% =============================================================================

guest(alice).
guest(bob).

dish(pasta).
dish(salad).
dish(steak).

cost(pasta, 8).
cost(salad, 5).
cost(steak, 20).

% Hard: each guest orders exactly one dish.
1 { order(G, D) : dish(D) } 1 :- guest(G).

% Soft: penalize expensive orders (lower total penalty is better).
:~ order(G, D), cost(D, C). [C@1, G, D]

#show order/2.
