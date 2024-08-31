# Spindle

spindle is a very minimal framework for building language model programs. i think that the hallmark of good tooling is that it enables users to write good code by default, and spindle is my attempt to do that for language model programs.

spindle takes some inspiration from dspy and moatless tools. it's also probably pretty generous to call this a framework -- it just makes it easier to write lm programs with prettier code (core lib is like 100loc with 0 dependencies)

## Usage

To install, run `pip install git+https://github.com/pranavnt/spindle`

## utilities

- text splitting utilities; probably worth having sadly
- GPT model wrapper; add support for generations, embeddings, json/structured generator, etc., ollama etc.

## TODO
- what if you want to have a "fork" module. i.e. if you want to have multiple return values or smth
