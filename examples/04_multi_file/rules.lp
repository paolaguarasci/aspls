% =============================================================================
% Tutorial 4 — Multi-file pool (facts + rules)
%
% Run with aspls: open rules.lp, use "Compute answer sets (config)".
%   aspls.clingo.json lists facts.lp in additionalFiles.
%
% CLI (PATH Clingo):  clingo examples/04_multi_file/facts.lp examples/04_multi_file/rules.lp 0
% =============================================================================

flies(X) :- bird(X), not penguin(X).

#show flies/1.
