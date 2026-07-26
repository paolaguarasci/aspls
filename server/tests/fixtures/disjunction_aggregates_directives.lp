#const n = 5.

color(1..n).

covered(X) ; uncovered(X) :- color(X).

:- #count{X : covered(X)} < 2.

#show covered/1.
