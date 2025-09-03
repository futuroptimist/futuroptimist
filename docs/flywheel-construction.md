# Flywheel Construction

Designing a flywheel means balancing energy storage against material limits.
This note captures the basic physics behind the CAD model used in Futuroptimist
prototypes. The disk in our CAD has

* outer radius $r_o = 75\,\text{mm}$ (150\,mm outer diameter)
* bore radius $r_i = 6\,\text{mm}$
* thickness $t = 10\,\text{mm}$

Aluminum 6061‑T6 has density $\rho \approx 2.70\,\text{g·cm}^{-3}$
($2.70\times10^{3}\,\text{kg·m}^{-3}$) and yield strength about
$276\,\text{MPa}$.

## Moment of inertia

For a uniform disk with inner radius $r_i$ and outer radius $r_o$:

\begin{aligned}
  m &= \rho\,\pi t (r_o^2 - r_i^2),\\
  I &= \tfrac12 m (r_o^2 + r_i^2).
\end{aligned}

The dimensions above yield a volume of $1.76\times10^{-4}\,\text{m}^3$ and a
mass of $0.47\,\text{kg}$. The corresponding moment of inertia is
$1.3\times10^{-3}\,\text{kg·m}^2$.

## Stored energy

A spinning flywheel stores kinetic energy proportional to the square of its
angular velocity $\omega$:

$$E = 0.5\, I \omega^2.$$

At 3 000 rpm ($\omega = 2\pi N$ with $N = \tfrac{3000}{60}\,\text{rev·s}^{-1}$,
so $\omega \approx 314\,\text{rad·s}^{-1}$) this flywheel stores about
$66\,\text{J}$ of kinetic energy.

## Torque and spin‑up

Torque relates angular acceleration $\alpha$ to inertia:

$$\tau = I\alpha.$$

For a constant spin‑up, $\alpha = \Delta\omega/\Delta t$. Bringing the disk from
rest to 3 000 rpm in $5\,\text{s}$ therefore requires roughly
$0.08\,\text{N·m}$ of torque.

## Stress check

Rotational speed is limited by the material's tensile strength.  For a solid
disk the maximum hoop stress occurs at the rim and can be approximated by

$$\sigma_\text{max} = \frac{3 + \nu}{8}\, \rho\, \omega^2 r_o^2,$$

where $\nu$ is Poisson's ratio (about 0.33 for 6061‑T6 aluminum) and $\rho$ is
the material density\footnote{See R. C. Hibbeler, *Engineering Mechanics:
Dynamics*, or Budynas & Nisbett, *Shigley's Mechanical Engineering Design*.}.
At 3 000 rpm the hoop stress is roughly $0.62\,\text{MPa}$, well below the
alloy's $276\,\text{MPa}$ yield strength. Compare the computed stress to the
material limit to set a safe operating speed.

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
