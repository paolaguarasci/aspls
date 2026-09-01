% =============================================================================
% Tutorial 1 — Facts, rules, and default negation
%
% Run:  clingo examples/01_basics/birds.lp 0
% Goal: see which birds can fly (all except penguins).
% =============================================================================

% Facts: ground atoms we know are true.
bird(tweety).
bird(pingu).
penguin(pingu).

% Rule: X flies if X is a bird and X is not a penguin.
% "not penguin(X)" is default negation — true when penguin(X) cannot be proved.
flies(X) :- bird(X), not penguin(X).

% Project only the flies/1 predicate in answer sets.
#show flies/1.
