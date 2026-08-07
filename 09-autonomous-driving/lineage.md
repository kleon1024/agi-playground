---
level: reference
---

# The open-source line behind autonomous driving

> Dated survey, 2026-08-07. Sources cited inline. External claims are not
> re-measured here; every repository claim cites the run that measured it.

**Question:** this topic's artifact is a low-resolution synthetic camera
render in, a steering/throttle action out, and a closed-loop episode that
either completes or collides. Where did imitation learning in simulation
come from, and what does the line say about where it stops?

## The modular autonomy stack

The classical production answer is modular: perception (detect lanes,
objects, drivable space), prediction (where will those objects move),
planning (choose a trajectory), and control (track it). **DARPA Grand
Challenge 2005** (Stanford's Stanley) proved the modular stack works at
speed on real roads, and the same decomposition still organizes most
production stacks. The cost of the modular stack is the interfaces:
each hand-designed module boundary is a place errors compound, which is
exactly the argument the end-to-end line makes.

## End-to-end and imitation learning

**ALVINN** (Pomerleau, 1989) trained a small neural network on camera
images to steer, the field's first demonstration that driving behavior can
be learned rather than engineered. The modern revival is
**NVIDIA DAVE-2** (Bojarski et al., 2016), which trained a CNN on
front-camera images and steering angles — behavior cloning from expert
demonstrations, the exact method this topic's stage 03 runs at toy scale.
The line's known failure is the one this topic measures: imitation learns
the expert's in-distribution behavior, and closed-loop evaluation is where
the gap shows, because small errors compound over time
**("compounding error" in imitation learning, formalized in Ross &
Bagnell, 2010's DAgger framing)**. DAgger's answer — query the expert on
the learner's own visited states — is the fix this topic deliberately does
not need at toy scale, because its expert is free to query, and it notes
that as the declared next rung.

## Simulation as the training ground

**CARLA** (Dosovitskiy et al., 2017) made photorealistic simulation a
standard training and evaluation ground; **Waymo Open Dataset** (2019) and
**nuScenes** (2020) made real logged data the evaluation complement.
**Wayve** (2017-2026) is the production-scale proponent of the
end-to-end learned stack this topic's toy version follows, and
**Tesla's FSD** (2020-2026) sits between the two lines, keeping a modular
architecture while replacing hand-written components with learned ones.
The repo's measured point is the discipline all three share: a claim about
driving behavior is only as honest as its closed-loop evaluation, which is
why this topic's primary metric is completion rate in the loop, not
imitation loss.

## Evidence boundary

Dated and attributed, not measured. The repo anchors — the closed-loop
completion rates, the imitation-vs-in-loop gap, the stage-05
generalization boundary — cite their runs. The line does not settle
whether modular or end-to-end "wins"; it says closed-loop evaluation and
out-of-distribution scenarios are the two things any autonomy claim has to
pay for, which is exactly why this topic asks them first.

