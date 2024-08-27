# Spindle

spindle is a very minimal framework for building language model programs, focused on simplicity and extensibility.

takes inspiration from dspy, moatless tools, and FP.

core ideas:
- a language model program is a series of modules that are composed together
- modules are functions that take in a state and return a new state and a next module (or None to terminate)
- you can optimize modules/programs via higher order functions
- LM frameworks should be quite minimal — users, not framework authors, should be writing the vast majority of modules

opinions behind this:
- modules should be pure functions, not classes
- higher order functions are the best abstraction for optimizing LM programs

it's probably pretty generous to call this a framework -- it just makes it easier to write lm programs with prettier code