https://github.com/JohnnyMarnell/iqe/tree/master/src/touch-designer/iqe-artnet-electron

Here is the typescript electron app subfolder we wrote that listens for ArtNet packets and renders them. It has a complex universe + channel => to pixel XY mapping system, for the 420 x 24 grid. (Markdown files elsewhere in the repo may also help you understand).

#1 Write a simple yaml file that describes the reverse: contiguous pixel ranges to contiguous universe + channel ranges.

#2 write the DAT / “table” format text that can be input into a Touch Designer nodes for DMX output that would correctly map and convert 420 x 24 pixel video screen into a stream of ArtNet.

#3 in addition to the table text, describe in detail the node structure to achieve this output in Touch Designer. It must honor the tricky universe and channel mapping scheme, as well as handle unpacking and reading the RGB values from a touch designer video node, and repacking and sending them as proper ArtNet bytes in correct universe and channels


# Summary

I am building a python system that will read bio metrics from
my [Muse headband](http://choosemuse.com/) and animate LEDs and
status GUIs.

For now, from you, I want two deliverables:
1. A README.md document for humans and our repo
2. An AGENTS.md document meant for AI agents like Cursor or
   Claude Code to read and gleen guidance for building

# Human Instruction README.md Document

This should have a "newb" section, where non-technical leaning
folks don't feel lost. It should cover setting up iTerm,
brew, GitHub Desktop App, `gh` command line, a repo, and
installing and running the python we build
(use `uv` and `pyproject.toml` for build config and run).

It should cover a general development workflow with Cursor IDE,
and being able to view, run, observe, and push changes to GitHub.

The README should also have sections describing overall
architecture and design decisions as we progress. Examples
could include key python classes, strategies for managing
Bluetooth LTE connections, receiving data from SDKs, and
synthesizing it into visuals. These end goal of these visuals
will be LED animation from a Pi Zero, however we want good logging
and internal HTML views as well!

# Agents Instruction Document

This document is tailored for an agent like Claude Code
(in its case, it's like a CLAUDE.md file) and should contain
notes useful for an LLM to immediately have context in the repo.

It should also include To Do lists of our next features we're
working on, and source code snippets and examples, for guidance.

**IMPORTANT**: In this first iteration, include many key class examples
in this document, and either their full source code,
or snippets and examples and psuedo code, for a more agentic
LLM to work off of later.

# Overal Design and Approach of Our Code

**IMPORTANT:** Use important notes already mentioned above
(e.g. `uv` was mentioned).

Muse has an SDK for its biometric hardware headband:
https://choosemuse.com/pages/developers

Our code should discover and seamlessly pair (whatever handshakes may
be necessary) over Bluetooth LTE to the headband.

The end result will interpret this streaming biometrics data,
in forms varying from more raw, device level, and/or
more derived, synthesized data. Follow the SDK's guidance on this.
It should then apply any necessary smoothing and use it
to influence animated LED pattern animation,
i.e. on wearables like a hat.

It may use systems like PixelBlaze or Chromatik for this,
but this will be a later step.

It should have an easy to run web UI for diagnostics
and status interpreations by humans. Think animating meters representing
some kind of mood level, or brain wave, or heartbeat pulses.
Read what's available from the SDK and make informed
decisions as to both possible low hanging fruit, plus
things that will play nicely in light animation.

Also make sure terminal logging is good (but not too verbose, we do not
want to overwhelm LLM context with too many tokens!), so we
can have easy, iterative development as a humand and with LLM agents.

Include one pytest integration test that can pair and verify
metrics received.