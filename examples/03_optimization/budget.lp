% =============================================================================
% Tutorial 3 — Optimization with #minimize
%
% Run:  clingo examples/03_optimization/budget.lp 0
% Goal: pick items within budget, minimizing total cost.
%
% Potassco Guide: Language §3.1 (#minimize); cf. §5.2 TSP cost minimization.
% See readme.md learning path.
% =============================================================================

#const budget = 10.

item(apple).
item(pear).
item(cheese).
cost(apple, 2).
cost(pear, 3).
cost(cheese, 8).

% Choose any subset of items (unbounded choice).
{ selected(X) : item(X) }.

% Hard constraint: total cost must not exceed the budget.
:- #sum{ C, X : selected(X), cost(X, C) } > budget.

% Soft objective: prefer lower total cost (lower is better).
#minimize { C@1, X : selected(X), cost(X, C) }.

#show selected/1.
