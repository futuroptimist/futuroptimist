# Sugarkube (working title) (2026-09-01)

> Draft script for video `<youtube_id>`

> Draft outline

> 0:00–0:40: physical hook, environmental concern, and honest thesis
> 0:40–1:30: deployment tax and SRE motivation
> 1:30–3:00: Sugarkube hardware, k3s platform, and command layer
> 3:00–5:55: DSPACE, token.place, and danielsmith.io as a connected ecosystem
> 5:55–10:05: measured electricity, AWS cost comparison, and the efficiency-versus-agency tension
> 10:05–11:15: participation and concluding vision

## Script

> 0:00–0:40: Physical hook, environmental concern, and honest thesis

AI feels like it lives in the cloud, but the cloud is physical. Data centers place concentrated demands on electrical grids; many use water for cooling, and nearby communities can feel those impacts. So I built this: Sugarkube, a bright-yellow rack of nine Raspberry Pis hosting my open-source projects. My goal is modest. I want to see, measure, and control more of the infrastructure behind my software, then find out how much that local control matters. I don’t expect this rack to replace the cloud or necessarily beat it on raw efficiency.

> 0:40–1:30: The deployment tax and my SRE motivation

I’ve spent more than a decade building production software, including nearly seven years as a site reliability engineer at YouTube. I’ve been on-call for large-scale, globally distributed systems, so I know reliable services require much more than writing code. My personal projects run at a much smaller scale, but they still need packaging, deployment, verification, updates, and recovery when something fails. I have way too many passion projects, as you can see on my GitHub, so every one-off deployment path takes time away from improving them. Sugarkube is my attempt to make that work boring and repeatable. Boring infrastructure is usually good infrastructure.

> 1:30–3:00: What Sugarkube actually is

Cloud platforms already make small app deployments relatively easy, especially with a trusty LLM whispering in your ear. I wanted a homegrown path built on Kubernetes.

Kubernetes coordinates containerized applications across one or more machines. You describe how an application should run, and Kubernetes places it, restarts it after failures, and rolls out updates.

Sugarkube runs k3s, a lightweight Kubernetes distribution suited to homelabs and single-board computers. The rack has three bright-yellow PLA tiers, each holding three Raspberry Pi 5s. One unmanaged PoE+ switch provides power and networking.

Only six Pis are active right now. Three form a staging cluster configured for high availability, and three form a separate production cluster configured the same way. A seventh will eventually handle ephemeral development builds without high availability. The last two are still unemployed. I haven’t decided what jobs to give them yet.

The repository includes the printable designs, tooling for a Raspberry Pi OS image with cloud-init and k3s preinstalled, and a command layer built around `just`. Its `justfile` packages commands into recipes that bootstrap clusters, onboard applications, deploy and verify them, promote artifacts to production, and roll them back. This makes routine workflows approachable while leaving the manifests, Helm charts, and infrastructure open for inspection and modification.

> 3:00–5:55: The ecosystem running through it

The rack is only interesting if it runs something. Today, Sugarkube is my deployment path for three public projects: DSPACE, token.place, and my portfolio site, danielsmith.io. Watch this list grow over the next few years.

First is DSPACE at democratized.space, a space exploration idle game that, incidentally, hasn’t made it to space yet. My wildly overambitious goal is to turn as much of the space exploration technology tree and its dependencies as I can into something educational and fun. Its quests span 3D printing, hydroponics, composting, electronics, robotics, astronomy, rocketry, and much more. Nearly four years in, I’m nowhere near finished. An explorable 3D version may come much later.

Second is token.place, my open-source distributed LLM inference platform. Its rate-limited public API currently requires no account, API key, or payment. Sugarkube hosts the relay, while people contribute spare compute by running models on consumer machines through a desktop app.

Requests are end-to-end encrypted between the client and the selected compute node. The relay sees ciphertext and limited routing metadata, but the compute node must decrypt the prompt for inference. This changes the trust boundary instead of eliminating trust.

Today, more nodes mostly mean more capacity. My long-term hypothesis is that a larger, more diverse pool of independently operated nodes, combined with verifiable work histories and Sybil resistance, could make it harder for a bad actor to dominate node selection. That reputation system does not exist yet.

By default, the official desktop app keeps prompt and response plaintext in memory and writes only redacted metadata to its logs. Compute nodes and relays can both be self-hosted, so the strongest privacy story is running hardware you control.

Third is danielsmith.io. It deploys as a static site, but that static site packs quite a punch. Three.js renders a decorated, lived-in house with two floors and a backyard. You guide an avatar between points of interest representing my projects, experience, and personality. The immersive experience includes a built-in tutorial. A dedicated text version serves visitors who prefer a conventional page or use screen readers. It gives hiring managers and recruiters a memorable first impression while whimsically capturing my interests in graphics programming and game development.

Together, these projects form a feedback loop. DSPACE uses token.place for its built-in LLM chat NPC, dChat. Sugarkube hosts the relay and deploys all three projects through one staged release workflow. danielsmith.io acts as the front door. Each application exposes another weakness in the shared infrastructure, and every fix makes them easier to ship.

> 5:55–10:05: Electricity measurement and the efficiency-versus-agency tension

My nine Raspberry Pi 5s each have 8 gigabytes of RAM, but only six are active, and even those are probably overkill for my traffic. I was lucky enough to buy everything before the current Rampocalypse was in full swing.

For a fair comparison, I disconnected the three unused Pis and measured the PoE+ switch, along with any external cooling used during normal operation, through a `<power meter model>`. Over `<measurement duration>` during `<representative conditions or workload>`, the setup averaged `<average watts>` watts, peaked at `<peak watts>` watts, and consumed `<measured kilowatt-hours>` kilowatt-hours.

Across an average 730-hour month, that becomes `<monthly kilowatt-hours>` kilowatt-hours. At my marginal electricity rate of `<electricity rate>` per kilowatt-hour, it costs `<monthly electricity cost>` per month, or `<annual electricity cost>` per year.

That includes the switch, PoE losses, and cooling used during the test. It excludes my shared router and modem, along with token.place compute nodes outside the rack. A separate GPU-enabled computer needs its own measurement.

For the cloud comparison, I modeled self-managed three-node staging and production clusters in one availability zone in AWS’s Oregon region. The single availability zone mirrors the rack’s single-site failure domain.

The model uses six on-demand Linux `c7g.xlarge` instances. Their four Arm vCPUs and 8 GiB of memory roughly match each Pi’s resource shape, although the AWS instances are substantially faster.

Each instance gets a 256 GiB gp3 volume and a public IPv4 address. I kept k3s and Cloudflare Tunnel, excluding EKS, a managed load balancer, a NAT gateway, RDS, and managed observability.

Using AWS’s public rates from July 22, 2026, compute costs $635.10 per month, storage costs $122.88, and IPv4 addresses cost $21.90. The fixed total is $779.88 per month, or $9,358.56 per year, before taxes, data transfer, snapshots, expanded monitoring, backups, or support.

Discounts, smaller instances, or shutting staging down could lower that bill substantially, but would change this always-on, shape-matched comparison.

AWS does not publish the direct power consumption of an individual instance, so this compares cost rather than watts. Its newer hardware and data-center economies may win on performance per watt, but this experiment did not prove that.

The full nine-node build cost me `<full nine-node BOM total>`. Excluding the three unused Pi node kits while retaining required shared equipment brought the comparable six-node cost to `<comparable six-node BOM total>`. The repository supplied the quantities; my receipts supplied the prices.

If local electricity costs less than $779.88 per month, simple cash break-even occurs after `<break-even months>` months. That is the comparable six-node cost divided by the monthly savings over AWS, rounded up. If local operating costs equal or exceed AWS, there is no positive break-even under these assumptions.

This calculation also ignores my labor, failures, replacement parts, internet service, AWS discounts, and the value of managed infrastructure. A real lifecycle comparison would need to include manufacturing, shipping, embodied energy, and indirect water use on both sides. The rack itself uses no cooling water, unless you count what I drank while assembling it. There is no dedicated air conditioning, humidity control, or liquid cooling; just onboard fans and a desk fan.

Running locally gives me more agency over energy use. I can meter the rack, choose its electricity source, schedule work around solar generation, power down unused environments, and own the means of production for this tiny corner of the internet. That control matters to me, even though it does not automatically make the homelab greener.

> 10:05–11:15: Participation and concluding vision

All four projects are open source. You can play DSPACE and suggest quests, explore danielsmith.io, run a token.place compute node or relay, or try Sugarkube on your own Raspberry Pis. Even testing the documentation and telling me where it breaks would help.

Very few people need a micro data center at home. You can start with one Pi or an old computer. This yellow rack isn’t going to defeat AWS in single combat. I want Sugarkube to provide another option where people can own more of the stack, learn Kubernetes by running something real, and decide how their hardware and energy are used.

Long term, I plan to run Sugarkube from a dedicated off-grid solar, battery, and inverter system. Subscribe if you want to see that process!

I started Sugarkube because deploying my projects kept getting in the way of building them. Now they form one connected ecosystem, and the infrastructure is helping me move faster. It’s visible, measurable, modifiable, and mine.