% =============================================================================
% Tutorial 2 — Choice rules (pick exactly one option)
%
% Run:  clingo examples/02_choice/menu.lp 0
% Goal: each guest picks exactly one main course from the menu.
% =============================================================================

guest(alice).
guest(bob).

dish(pasta).
dish(salad).
dish(soup).

% For each guest G, choose exactly one dish D from the menu.
1 { order(G, D) : dish(D) } 1 :- guest(G).

% Integrity constraint: forbid ordering a dish that is not on the menu.
:- order(_, D), not dish(D).

#show order/2.
