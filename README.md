# Spindle

spindle is a very minimal framework for building language model programs. i think that the hallmark of good tooling is that it enables users to write good code by default, and spindle is my attempt to do that for language model programs.

spindle takes some inspiration from dspy and moatless tools (i really like the way dspy frames lm programming). it's also probably pretty generous to call this a framework -- it just makes it easier to write lm programs with prettier code (core lib is like 100loc with 0 dependencies)

core ideas (basically just "oop bad"):
- your language model program is a composition of modules — pure functions that take in a state and return a new state and a next module (or None to terminate)
- higher order functions are the best abstraction for lm program optimization

## Usage

To install, run `pip install git+https://github.com/pranavnt/spindle`

## utilities

- text splitting utilities; probably worth having sadly
- GPT model wrapper; add support for generations, embeddings, json/structured generator, etc., ollama etc.
