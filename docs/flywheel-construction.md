# Flywheel Construction

Designing a flywheel means balancing energy storage against material limits.
This note captures the basic physics behind the CAD model used in Futuroptimist
prototypes. The disk in our CAD has

* outer radius $r_o = 75\,\text{mm}$
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

At 3 000 rpm (314 rad/s) this flywheel stores about $66\,\text{J}$ of kinetic
energy.

## Torque and spin‑up

Torque relates angular acceleration $\alpha$ to inertia:

$$\tau = I\alpha.$$

Spinning the disk from rest to 3 000 rpm in $5\,\text{s}$ requires roughly
$0.08\,\text{N·m}$ of torque.

## Stress check

Rotational speed is limited by the material's tensile strength.  The approximate
hoop stress for a solid disk is

$$\sigma \approx (\rho \omega^2 r^2)/3,$$

where $\rho$ is the material density. At 3 000 rpm the stress is about
$0.5\,\text{MPa}$, well below the alloy's $276\,\text{MPa}$ yield strength.
Compare the computed stress to the material limit to set a safe operating speed.

Setting $\sigma$ equal to the alloy's yield strength $\sigma_y$ and solving for
angular velocity gives a conservative limit,

$$\omega_{\max} \approx \sqrt{\frac{3\sigma_y}{\rho r_o^2}}.$$
For $\sigma_y = 276\,\text{MPa}$ and $r_o = 75\,\text{mm}$, the maximum speed is
about $7.4\times10^3\,\text{rad·s}^{-1}$ (roughly $70\,000\,\text{rpm}$).
Designers typically apply a safety factor to this value to account for fatigue
and manufacturing tolerances.


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
