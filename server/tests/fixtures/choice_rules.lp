% Bounded choice with conditional elements
candidate(1).
candidate(2).
candidate(3).
1 { chosen(X) : candidate(X) } 1.

% Unbounded multi-element choice fact
{ a; b }.

% Unbounded conditional choice
item(apple).
item(pear).
{ selected(X) : item(X) }.

% Choice head with rule body
ok.
1 { picked(X) : candidate(X) } 1 :- ok.

#show chosen/1.
#show selected/1.
#show picked/1.
