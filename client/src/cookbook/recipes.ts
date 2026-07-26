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
];
