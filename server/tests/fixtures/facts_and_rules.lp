% a simple fact
bird(tweety).
penguin(pingu).

% a rule with negation as failure
flies(X) :- bird(X), not penguin(X).
