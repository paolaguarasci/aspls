item(a).
item(b).
{ selected(X) : item(X) }.
#minimize { 1@1, X : selected(X) }.
#minimize { W@2, X : selected(X), weight(X, W) ; 1, X : bonus(X) }.
