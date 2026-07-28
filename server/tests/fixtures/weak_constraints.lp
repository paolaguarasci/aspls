item(a).
item(b).
expensive(a).

{ selected(X) : item(X) }.
:~ selected(X), expensive(X). [1@1, X]
:~ selected(X). [2@2]
:~ selected(a). [1]
