# Flywheel Construction

Designing a flywheel means balancing energy storage against material limits.
This note captures the basic physics behind the CAD model used in Futuroptimist
prototypes.

## Moment of inertia

For a solid disk with mass $m$ and outer radius $r$ the moment of inertia is

$$I = 0.5\, m r^2.$$

Our CAD shows a 150 mm diameter, 10 mm thick aluminum disk with an 12 mm bore for
the shaft.  Assuming a mass of 0.9 kg, the moment of inertia is roughly
$2.5\times10^{-3}\,\text{kg·m}^2$.

## Stored energy

A spinning flywheel stores kinetic energy proportional to the square of its
angular velocity $\omega$:

$$E = 0.5\, I \omega^2.$$

At 3 000 rpm (314 rad/s) the example above holds about 120 J.

## Stress check

Rotational speed is limited by the material's tensile strength.  The approximate
hoop stress for a solid disk is

$$\sigma \approx (\rho \omega^2 r^2)/3,$$

where $\rho$ is the material density.  Compare this value to the alloy's yield
stress to set a safe operating speed.

```
    outer radius r
      ┌────────────┐
      │            │  thickness t = 10 mm
      │            │
      └───┬──┬─────┘
          │  │
          ╰──╯ bore = 12 mm
```

The sketch above mirrors the CAD cross‑section to emphasize how dimensions map
onto the formulas.
