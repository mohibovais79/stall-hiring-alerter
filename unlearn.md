# What I Unlearned


## How I used to work
I take an idea, drop a prompt on a coding agent, and start building, often in
auto mode. It is fast, but it has two problems I wanted to fix. I end up
designing around what I want to code instead of what the user needs, and I
review a black box at the end, so I have little control over what the agent
actually wrote or why.

## Habit 1: prompt-first building
**Before:** idea, prompt, build.
**Now:** user stories first. I wrote stories.md with acceptance criteria
before writing any code, and designed each feature from a story. The first
question became "what does the recruiter need?" and not "what can I build
quickly?". This also forced me to make decisions I would normally have left to
the agent. For example, I decided that a row with a corrupt date is rejected
even if its status says Hired or Rejected, so bad data surfaces as a data
problem and does not quietly inflate an "inactive" count. I made that call in
the spec, before any code existed.

## Habit 2: black-box agent coding
**Before:** let the agent run in auto mode and review the result at the end.
**Now:** test-driven development with AI. I set the process in directive.md:
one story at a time, tests proposed from the acceptance criteria and approved
by me first, tests shown failing, then the minimum code to pass. The point was
control. A test written from a criterion I understand is a check on the
agent that does not depend on trusting the agent. I also made the agent bound
by written rules, including not claiming anything ran unless it showed the
output, so my expectations were explicit rather than assumed.

## What changed in how I think
The biggest shift is where I spend effort. Before, most of it went into
prompting and fixing. Now more of it goes into the spec and the review, and
less into the code itself. The documents (intent.md, stories.md, directive.md)
became the place where I steer the work, and the agent became a pair I direct
rather than a tool I hand a goal to.

## What I am not claiming
This was one small project built over two working days That is enough to try the new process and see it
work, but it is not proof that the habits have changed for good. The real test
is whether I start the next project from stories and tests without being asked
to. That is my intention.
