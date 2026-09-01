export type CookbookRecipe = {
  id: string;
  title: string;
  category: string;
  description: string;
  code: string;
};

/**
 * In-editor cookbook of working ASP patterns for newcomers.
 * Distinct from snippets (prefix templates): these are complete fragments.
 */
export const COOKBOOK_RECIPES: readonly CookbookRecipe[] = [
  {
    id: "basics-facts-rules",
    title: "Facts and rules (birds / penguins)",
    category: "Basics",
    description: "Facts, default negation, and a derived predicate",
    code: `% Birds fly unless they are penguins
bird(tweety).
bird(pingu).
penguin(pingu).

flies(X) :- bird(X), not penguin(X).

#show flies/1.`,
  },
  {
    id: "basics-ranges",
    title: "Domains with ranges",
    category: "Basics",
    description: "Integer ranges bound by #const",
    code: `% Domain from a constant
#const n = 3.

domain(1..n).
cell(X) :- domain(X).

#show cell/1.`,
  },
  {
    id: "choice-exact-one",
    title: "Choice rule (pick exactly one)",
    category: "Choice",
    description: "Bounded choice over a domain",
    code: `% Choose exactly one candidate
candidate(1).
candidate(2).
candidate(3).

1 { chosen(X) : candidate(X) } 1.

#show chosen/1.`,
  },
  {
    id: "choice-disjunction",
    title: "Head disjunction",
    category: "Choice",
    description: "Exclusive alternatives in the head",
    code: `% Each candidate is chosen or rejected
candidate(a).
candidate(b).

chosen(X) ; rejected(X) :- candidate(X).

#show chosen/1.
#show rejected/1.`,
  },
  {
    id: "constraints-integrity",
    title: "Integrity constraint",
    category: "Constraints",
    description: "Forbid incompatible combinations",
    code: `% At most one of a or b
{ a; b }.
:- a, b.

#show a/0.
#show b/0.`,
  },
  {
    id: "aggregates-count",
    title: "Count aggregate",
    category: "Aggregates",
    description: "Bind and compare #count",
    code: `% Count nodes and require at least one
node(a).
node(b).
node(c).

num_nodes(N) :- N = #count{ X : node(X) }.
has_nodes :- #count{ X : node(X) } > 0.

#show num_nodes/1.
#show has_nodes/0.`,
  },
  {
    id: "aggregates-sum",
    title: "Sum aggregate",
    category: "Aggregates",
    description: "Total weight with #sum",
    code: `% Sum weights of selected items
item(apple).
item(pear).
weight(apple, 2).
weight(pear, 3).

{ selected(X) : item(X) }.
total(S) :- S = #sum{ W, X : selected(X), weight(X, W) }.

#show selected/1.
#show total/1.`,
  },
  {
    id: "optimization-minimize",
    title: "Minimize directive",
    category: "Optimization",
    description: "Prefer lower-cost chosen atoms",
    code: `% Prefer cheaper choices
option(a).
option(b).
cost(a, 3).
cost(b, 1).

1 { chosen(X) : option(X) } 1.
#minimize { C@1, X : chosen(X), cost(X, C) }.

#show chosen/1.`,
  },
  {
    id: "optimization-weak",
    title: "Weak constraint",
    category: "Optimization",
    description: "Soft preference with :~",
    code: `% Softly prefer not selecting expensive items
item(a).
item(b).
expensive(a).

{ selected(X) : item(X) }.
:~ selected(X), expensive(X). [1@1, X]

#show selected/1.`,
  },
  {
    id: "directives-const-show",
    title: "#const and #show",
    category: "Directives",
    description: "Name a constant and project output",
    code: `% Named constant and projected predicates
#const width = 2.

cell(1..width).
label(hello).

#show cell/1.
#show label/1.`,
  },
  {
    id: "graphs-coloring",
    title: "Graph 3-coloring",
    category: "Graphs",
    description: "Assign colors so adjacent nodes differ",
    code: `% Undirected edges; each node gets exactly one color
edge(1, 2). edge(2, 3). edge(3, 1). edge(1, 4).
edge(X, Y) :- edge(Y, X).

node(X) :- edge(X, _).
node(X) :- edge(_, X).

color(red; green; blue).

1 { colored(N, C) : color(C) } 1 :- node(N).

:- edge(X, Y), colored(X, C), colored(Y, C).

#show colored/2.`,
  },
  {
    id: "scheduling-capacity",
    title: "Job scheduling with capacity",
    category: "Scheduling",
    description: "Assign jobs to days under a daily load cap",
    code: `% Each job starts on one day; total duration per day is bounded
job(a; b; c).
day(1..5).
duration(a, 2). duration(b, 1). duration(c, 2).
#const cap = 2.

1 { start(J, D) : day(D) } 1 :- job(J).

load(D, L) :- L = #sum{ Dur, J : start(J, D), duration(J, Dur) }.
:- load(D, L), L > cap.

#show start/2.`,
  },
  {
    id: "scheduling-precedence",
    title: "Scheduling with precedences",
    category: "Scheduling",
    description: "Order jobs on slots respecting before/after links",
    code: `% Each job gets a slot; precedences must be respected
job(a; b; c).
pre(a, b).
pre(b, c).
slot(1..3).

1 { assign(J, S) : slot(S) } 1 :- job(J).

:- pre(J1, J2), assign(J1, S1), assign(J2, S2), S1 >= S2.

#show assign/2.`,
  },
  {
    id: "puzzles-sudoku-4x4",
    title: "4x4 Sudoku",
    category: "Puzzles",
    description: "One value per cell; unique in rows, columns, and 2x2 boxes",
    code: `% Mini Sudoku with a few givens
#const n = 4.
val(1..n).
cell(R, C) :- R = 1..n, C = 1..n.

1 { value(R, C, V) : val(V) } 1 :- cell(R, C).

:- value(R, C1, V), value(R, C2, V), C1 < C2.
:- value(R1, C, V), value(R2, C, V), R1 < R2.
:- value(R1, C1, V), value(R2, C2, V),
   (R1 - 1) / 2 = (R2 - 1) / 2, (C1 - 1) / 2 = (C2 - 1) / 2,
   R1 != R2, C1 != C2.

value(1, 1, 2).
value(2, 2, 4).

#show value/3.`,
  },
  {
    id: "planning-strips-schema",
    title: "STRIPS action schema",
    category: "Planning",
    description: "Declare actions with preconditions, add and delete lists",
    code: `% Blocks-world style STRIPS operators (schema only)
block(a; b).

action(grab(X)) :- block(X).
pre(grab(X), clear(X)) :- action(grab(X)).
pre(grab(X), ontable(X)) :- action(grab(X)).
add(grab(X), holding(X)) :- action(grab(X)).
del(grab(X), clear(X)) :- action(grab(X)).
del(grab(X), ontable(X)) :- action(grab(X)).

action(putdown(X)) :- block(X).
pre(putdown(X), holding(X)) :- action(putdown(X)).
add(putdown(X), ontable(X)) :- action(putdown(X)).
add(putdown(X), clear(X)) :- action(putdown(X)).
del(putdown(X), holding(X)) :- action(putdown(X)).

#show action/1.
#show pre/2.
#show add/2.
#show del/2.`,
  },
  {
    id: "planning-horizon",
    title: "Bounded planning horizon",
    category: "Planning",
    description: "STRIPS-like move actions to reach a goal within T steps",
    code: `% Move a token along a line until it reaches the goal
#const horizon = 3.
step(0..horizon).

loc(a; b; c).
at(a, 0).

action(go(L), S) :- loc(L), step(S), S < horizon.

{ occurs(A, S) : action(A, S) } 1 :- step(S), S < horizon.

at(L, S + 1) :- occurs(go(L), S), step(S).
at(L, S + 1) :- at(L, S), step(S), not occurs(go(_), S).

goal :- at(c, horizon).
:- step(horizon), not goal.

#show occurs/2.
#show at/2.`,
  },
];
