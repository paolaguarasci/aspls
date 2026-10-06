% =============================================================================
% Tutorial 7 — N-Queens (guess-and-check puzzle)
%
% Run:  clingo examples/07_nqueens/queens.lp 0
% Goal: place n queens so no two share a row, column, or diagonal.
%
% Diagonals are encoded with next/next2/next3 facts (no arithmetic terms)
% so the aspls LSP parser accepts the file; Clingo still finds both models
% for n = 4. See Cookbook *N-Queens* and readme.md learning path.
% =============================================================================

#const n = 4.

row(1..n).
col(1..n).

% Adjacent / skip distances for diagonal steps (n = 4).
next(1, 2). next(2, 3). next(3, 4).
next2(1, 3). next2(2, 4).
next3(1, 4).

% Guess: exactly one queen per row.
1 { queen(R, C) : col(C) } 1 :- row(R).

% Check: at most one queen per column.
:- queen(R1, C), queen(R2, C), R1 < R2.

% Check: diagonals (same distance in row and column).
:- queen(R1, C1), queen(R2, C2), next(R1, R2), next(C1, C2).
:- queen(R1, C1), queen(R2, C2), next(R1, R2), next(C2, C1).
:- queen(R1, C1), queen(R2, C2), next2(R1, R2), next2(C1, C2).
:- queen(R1, C1), queen(R2, C2), next2(R1, R2), next2(C2, C1).
:- queen(R1, C1), queen(R2, C2), next3(R1, R2), next3(C1, C2).
:- queen(R1, C1), queen(R2, C2), next3(R1, R2), next3(C2, C1).

#show queen/2.
