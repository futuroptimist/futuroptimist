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

[NARRATOR]: AI feels like it lives in the cloud, but the cloud is physical. Data centers place concentrated demands on electrical grids; many use water for cooling, and nearby communities can feel those impacts.

[VISUAL]: Open on macro close-ups of the bright-yellow Sugarkube rack: Raspberry Pi LEDs blinking, cooling fans spinning, Ethernet cables bundled into the PoE+ switch, and a slow tilt showing all three tiers. Cut to appropriately licensed stock footage of data-center interiors, electrical substations, cooling equipment, and water infrastructure. Label stock footage as illustrative cloud infrastructure, not a specific facility impact claim.

[NARRATOR]: So I built this: Sugarkube, a bright-yellow rack of nine Raspberry Pis hosting my open-source projects.

[VISUAL]: Return to a clean rack hero shot on Daniel's desk or workbench. Add a small on-screen label: "Sugarkube: 9 Raspberry Pi 5 slots".

[NARRATOR]: My goal is modest. I want to see, measure, and control more of the infrastructure behind my software, then find out how much that local control matters. I don’t expect this rack to replace the cloud or necessarily beat it on raw efficiency.

[VISUAL]: A-roll of Daniel at his desk using the teleprompter, with the rack visible beside him. Add restrained on-screen text: "Visible. Measurable. Modifiable." Then hold on A-roll for the efficiency caveat.

> 0:40–1:30: The deployment tax and my SRE motivation

[NARRATOR]: I’ve spent more than a decade building production software, including nearly seven years as a site reliability engineer at YouTube. I’ve been on-call for large-scale, globally distributed systems, so I know reliable services require much more than writing code.

[VISUAL]: A-roll at Daniel's desk. Use a neutral lower-third: "Daniel Smith, software engineer and SRE background". Do not show private or internal Google or YouTube material.

[NARRATOR]: My personal projects run at a much smaller scale, but they still need packaging, deployment, verification, updates, and recovery when something fails. I have way too many passion projects, as you can see on my GitHub, so every one-off deployment path takes time away from improving them.

[VISUAL]: Screen recording of Daniel's public GitHub profile and project repositories, then a practical montage of CI checks, terminal deploy commands, verification output, update notes, and rollback commands. Blur or crop secrets, tokens, private hostnames, and sensitive terminal history.

[NARRATOR]: Sugarkube is my attempt to make that work boring and repeatable. Boring infrastructure is usually good infrastructure.

[VISUAL]: Screen recording of a successful repeatable deployment workflow ending in green checks, then a quiet shot of the rack running steadily.

> 1:30–3:00: What Sugarkube actually is

[NARRATOR]: Cloud platforms already make small app deployments relatively easy, especially with a trusty LLM whispering in your ear. I wanted a homegrown path built on Kubernetes.

[VISUAL]: A-roll for the motivation, then cut to a simple title card: "Homegrown Kubernetes path" over a desktop shot of the rack and laptop.

[NARRATOR]: Kubernetes coordinates containerized applications across one or more machines. You describe how an application should run, and Kubernetes places it, restarts it after failures, and rolls out updates.

[VISUAL]: Simple editor-made diagram: containers distributed across one or more machines. Animate or label three steps: "place workload", "restart after failure", and "rolling update". Keep the diagram schematic and not product-specific.

[NARRATOR]: Sugarkube runs k3s, a lightweight Kubernetes distribution suited to homelabs and single-board computers. The rack has three bright-yellow PLA tiers, each holding three Raspberry Pi 5s. One unmanaged PoE+ switch provides power and networking.

[VISUAL]: Wide shot and close-ups of the rack, individual Pi 5 boards, the three printed PLA tiers, storage hardware, PoE+ switch, Ethernet cables, fans, and the office placement. Add labels for "k3s", "Raspberry Pi 5", "PLA tier", and "PoE+ power + networking".

[NARRATOR]: Only six Pis are active right now. Three form a staging cluster configured for high availability, and three form a separate production cluster configured the same way. A seventh will eventually handle ephemeral development builds without high availability. The last two are still unemployed. I haven’t decided what jobs to give them yet.

[VISUAL]: Nine-slot rack overlay on the real rack: three active staging nodes, three active production nodes, one clearly labeled "future dev node", and two clearly labeled "unassigned". Use distinct styling so future and unassigned nodes are not mistaken for active capacity.

[NARRATOR]: The repository includes the printable designs, tooling for a Raspberry Pi OS image with cloud-init and k3s preinstalled, and a command layer built around `just`. Its `justfile` packages commands into recipes that bootstrap clusters, onboard applications, deploy and verify them, promote artifacts to production, and roll them back. This makes routine workflows approachable while leaving the manifests, Helm charts, and infrastructure open for inspection and modification.

[VISUAL]: Screen recording of the Sugarkube repository: printable design files, image-building tooling, `justfile`, manifests, Helm charts, and docs. Show representative `just` commands for bootstrap, deploy, verify, promote, and rollback in a clean terminal with secrets and private values removed.

> 3:00–5:55: The ecosystem running through it

[NARRATOR]: The rack is only interesting if it runs something. Today, Sugarkube is my deployment path for three public projects: DSPACE, token.place, and my portfolio site, danielsmith.io. Watch this list grow over the next few years.

[VISUAL]: Simple editor-made ecosystem diagram with Sugarkube at the center and three current project nodes: DSPACE, token.place, and danielsmith.io. Add a small "future projects" placeholder, clearly marked as future.

[NARRATOR]: First is DSPACE at democratized.space, a space exploration idle game that, incidentally, hasn’t made it to space yet. My wildly overambitious goal is to turn as much of the space exploration technology tree and its dependencies as I can into something educational and fun.

[VISUAL]: Screen recording of the live DSPACE site landing page and gameplay loop. Cut back to A-roll for the joke if the timing lands better.

[NARRATOR]: Its quests span 3D printing, hydroponics, composting, electronics, robotics, astronomy, rocketry, and much more. Nearly four years in, I’m nowhere near finished. An explorable 3D version may come much later.

[VISUAL]: Screen recordings of DSPACE quest trees and representative content for 3D printing, hydroponics, composting, electronics, robotics, astronomy, and rocketry. For the explorable 3D version, use A-roll or a plain on-screen label "future concept, not implemented yet" rather than an invented mockup.

[NARRATOR]: Second is token.place, my open-source distributed LLM inference platform. Its rate-limited public API currently requires no account, API key, or payment. Sugarkube hosts the relay, while people contribute spare compute by running models on consumer machines through a desktop app.

[VISUAL]: Screen recording of the token.place public API documentation, the desktop compute-node app, and the real operator workflow for starting or monitoring a node. Include a small diagram showing Sugarkube hosting the relay and consumer machines contributing compute.

[NARRATOR]: Requests are end-to-end encrypted between the client and the selected compute node. The relay sees ciphertext and limited routing metadata, but the compute node must decrypt the prompt for inference. This changes the trust boundary instead of eliminating trust.

[VISUAL]: Simple custom diagram with three boxes: client, relay, selected compute node. Animate ciphertext passing through the relay and plaintext appearing only at the selected compute node. Return to A-roll for the trust-boundary caveat.

[NARRATOR]: Today, more nodes mostly mean more capacity. My long-term hypothesis is that a larger, more diverse pool of independently operated nodes, combined with verifiable work histories and Sybil resistance, could make it harder for a bad actor to dominate node selection. That reputation system does not exist yet.

[VISUAL]: Start with a real current-node capacity diagram labeled "today: more nodes, more capacity". Then switch to a clearly labeled future concept diagram of diverse independent nodes accumulating verified work histories. Add on-screen text: "That reputation system does not exist yet." Do not imply this exists today.

[NARRATOR]: By default, the official desktop app keeps prompt and response plaintext in memory and writes only redacted metadata to its logs. Compute nodes and relays can both be self-hosted, so the strongest privacy story is running hardware you control.

[VISUAL]: A-roll for the nuanced privacy caveat. Cut to real app settings, logs with redacted metadata, and repository documentation for self-hosted relay and compute-node options where those interfaces or docs exist.

[NARRATOR]: Third is danielsmith.io. It deploys as a static site, but that static site packs quite a punch. Three.js renders a decorated, lived-in house with two floors and a backyard. You guide an avatar between points of interest representing my projects, experience, and personality.

[VISUAL]: Screen recording of danielsmith.io loading, the Three.js house, avatar movement, both floors, backyard, and points of interest. Use smooth cursor movement and no private browser data.

[NARRATOR]: The immersive experience includes a built-in tutorial. A dedicated text version serves visitors who prefer a conventional page or use screen readers. It gives hiring managers and recruiters a memorable first impression while whimsically capturing my interests in graphics programming and game development.

[VISUAL]: Show the in-site tutorial, then separately show the dedicated text version with conventional navigation. Include a brief accessibility-focused shot of headings or navigation structure without pretending to demonstrate a specific screen reader if not recorded.

[NARRATOR]: Together, these projects form a feedback loop. DSPACE uses token.place for its built-in LLM chat NPC, dChat. Sugarkube hosts the relay and deploys all three projects through one staged release workflow. danielsmith.io acts as the front door. Each application exposes another weakness in the shared infrastructure, and every fix makes them easier to ship.

[VISUAL]: Editor-made connected ecosystem diagram: Sugarkube deploys DSPACE, token.place, and danielsmith.io; Sugarkube hosts the token.place relay; token.place powers DSPACE's dChat; danielsmith.io serves as the front door. Animate the feedback loop between app needs and infrastructure improvements.

> 5:55–10:05: Electricity measurement and the efficiency-versus-agency tension

[NARRATOR]: My nine Raspberry Pi 5s each have 8 gigabytes of RAM, but only six are active, and even those are probably overkill for my traffic. I was lucky enough to buy everything before the current Rampocalypse was in full swing.

[VISUAL]: Close-ups of Pi 5 boards and the nine-slot overlay again, with active nodes highlighted. Add restrained on-screen text: "9 Pi 5s, 8 GB each; 6 active". Cut to A-roll for the Rampocalypse joke.

[NARRATOR]: For a fair comparison, I disconnected the three unused Pis and measured the PoE+ switch, along with any external cooling used during normal operation, through a `<power meter model>`. Over `<measurement duration>` during `<representative conditions or workload>`, the setup averaged `<average watts>` watts, peaked at `<peak watts>` watts, and consumed `<measured kilowatt-hours>` kilowatt-hours.

[VISUAL]: Show Daniel disconnecting the three unused Pis. Show the PoE+ switch and continuously running desk fan clearly inside the measurement boundary, both connected through or represented in the `<power meter model>` setup. Capture the meter display or logging interface at idle and during the representative workload. Use on-screen placeholders for measured values until Daniel supplies final numbers.

[NARRATOR]: Across an average 730-hour month, that becomes `<monthly kilowatt-hours>` kilowatt-hours. At my marginal electricity rate of `<electricity rate>` per kilowatt-hour, it costs `<monthly electricity cost>` per month, or `<annual electricity cost>` per year.

[VISUAL]: Simple calculation graphic: average watts to monthly kWh over 730 hours, then electricity rate to monthly and annual cost. Keep the script placeholders visible and replace them only when final measurements are available.

[NARRATOR]: That includes the switch, PoE losses, and cooling used during the test. It excludes my shared router and modem, along with token.place compute nodes outside the rack. A separate GPU-enabled computer needs its own measurement.

[VISUAL]: Measurement-boundary diagram: include rack, PoE+ switch, PoE losses, onboard fans, and continuously running desk fan. Place router, modem, off-rack token.place compute nodes, and separate GPU computer outside the boundary with an "excluded" label.

[NARRATOR]: For the cloud comparison, I modeled self-managed three-node staging and production clusters in one availability zone in AWS’s Oregon region. The single availability zone mirrors the rack’s single-site failure domain.

[VISUAL]: Screen recording of the AWS calculator or a clean editor-made architecture diagram showing two self-managed three-node k3s clusters in one Oregon availability zone. Label the shared single-site failure-domain assumption.

[NARRATOR]: The model uses six on-demand Linux `c7g.xlarge` instances. Their four Arm vCPUs and 8 GiB of memory roughly match each Pi’s resource shape, although the AWS instances are substantially faster.

[VISUAL]: Table or diagram with six `c7g.xlarge` instances beside six active Pi nodes. Highlight "4 Arm vCPU, 8 GiB" and add a note: "shape-matched, AWS faster".

[NARRATOR]: Each instance gets a 256 GiB gp3 volume and a public IPv4 address. I kept k3s and Cloudflare Tunnel, excluding EKS, a managed load balancer, a NAT gateway, RDS, and managed observability.

[VISUAL]: Add six 256 GiB gp3 volumes and six public IPv4 address labels to the AWS architecture diagram. Show concise exclusions list: "No EKS, managed LB, NAT gateway, RDS, managed observability".

[NARRATOR]: Using AWS’s public rates from July 22, 2026, compute costs $635.10 per month, storage costs $122.88, and IPv4 addresses cost $21.90. The fixed total is $779.88 per month, or $9,358.56 per year, before taxes, data transfer, snapshots, expanded monitoring, backups, or support.

[VISUAL]: Readable pricing table or animated cost stack labeled "AWS public rates snapshot: July 22, 2026". Rows: compute $635.10, storage $122.88, IPv4 $21.90, total $779.88/month and $9,358.56/year. Add concise exclusions list: taxes, data transfer, snapshots, expanded monitoring, backups, support.

[NARRATOR]: Discounts, smaller instances, or shutting staging down could lower that bill substantially, but would change this always-on, shape-matched comparison.

[VISUAL]: A-roll for the caveat, with optional small on-screen note: "Different assumptions, different bill".

[NARRATOR]: AWS does not publish the direct power consumption of an individual instance, so this compares cost rather than watts. Its newer hardware and data-center economies may win on performance per watt, but this experiment did not prove that.

[VISUAL]: A-roll for the distinction between financial comparison and watt-for-watt energy comparison. Reinforce with on-screen text: "Cost comparison, not direct power measurement".

[NARRATOR]: The full nine-node build cost me `<full nine-node BOM total>`. Excluding the three unused Pi node kits while retaining required shared equipment brought the comparable six-node cost to `<comparable six-node BOM total>`. The repository supplied the quantities; my receipts supplied the prices.

[VISUAL]: Real hardware and printed parts laid out on a desk, cabling and storage close-ups, receipts with sensitive information redacted, and the repository BOM. Create a simple comparison card: full nine-node total vs comparable six-node total, preserving placeholders until final prices are inserted.

[NARRATOR]: If local electricity costs less than $779.88 per month, simple cash break-even occurs after `<break-even months>` months. That is the comparable six-node cost divided by the monthly savings over AWS, rounded up. If local operating costs equal or exceed AWS, there is no positive break-even under these assumptions.

[VISUAL]: Show the break-even formula on screen: `comparable six-node cost / (AWS monthly cost - local monthly electricity cost)`. Optionally add a simple cumulative-cost line chart with the crossing point at `<break-even months>`, plus a separate "no positive break-even" branch when local operating cost equals or exceeds AWS.

[NARRATOR]: This calculation also ignores my labor, failures, replacement parts, internet service, AWS discounts, and the value of managed infrastructure. A real lifecycle comparison would need to include manufacturing, shipping, embodied energy, and indirect water use on both sides.

[VISUAL]: A-roll for the lifecycle limitation. Use a compact on-screen list of omitted factors, then illustrative licensed footage of manufacturing, shipping, grid infrastructure, and data-center water systems labeled as lifecycle factors, not measured impacts.

[NARRATOR]: The rack itself uses no cooling water, unless you count what I drank while assembling it. There is no dedicated air conditioning, humidity control, or liquid cooling; just onboard fans and a desk fan.

[VISUAL]: Real shot of Daniel taking a drink for the joke. Cut to close-ups of onboard fans and the continuously running desk fan. Avoid implying there is no indirect water use from grid electricity, manufacturing, or cloud infrastructure.

[NARRATOR]: Running locally gives me more agency over energy use. I can meter the rack, choose its electricity source, schedule work around solar generation, power down unused environments, and own the means of production for this tiny corner of the internet. That control matters to me, even though it does not automatically make the homelab greener.

[VISUAL]: Show the power meter, rack controls, deployment dashboard or terminal workflows, and environments being powered down. Use A-roll for the caveat that control does not automatically mean greener.

> 10:05–11:15: Participation and concluding vision

[NARRATOR]: All four projects are open source. You can play DSPACE and suggest quests, explore danielsmith.io, run a token.place compute node or relay, or try Sugarkube on your own Raspberry Pis. Even testing the documentation and telling me where it breaks would help.

[VISUAL]: Montage of the four public project repositories and applications: DSPACE gameplay and quest suggestions, danielsmith.io exploration and text version, token.place compute-node or relay docs, and Sugarkube Raspberry Pi setup docs. Add restrained on-screen text: "Play, explore, run, test, report bugs".

[NARRATOR]: Very few people need a micro data center at home. You can start with one Pi or an old computer. This yellow rack isn’t going to defeat AWS in single combat. I want Sugarkube to provide another option where people can own more of the stack, learn Kubernetes by running something real, and decide how their hardware and energy are used.

[VISUAL]: A-roll for the grounded caveat and AWS joke. Cut to a single Pi or old computer beside the rack, then a clean shot of Kubernetes commands deploying something real.

[NARRATOR]: Long term, I plan to run Sugarkube from a dedicated off-grid solar, battery, and inverter system. Subscribe if you want to see that process!

[VISUAL]: Real or appropriately licensed stock footage of solar panels, battery storage, and an inverter, clearly labeled "future off-grid plan". Pair the subscription call to action with restrained on-screen text: "Subscribe for the off-grid build".

[NARRATOR]: I started Sugarkube because deploying my projects kept getting in the way of building them. Now they form one connected ecosystem, and the infrastructure is helping me move faster. It’s visible, measurable, modifiable, and mine.

[VISUAL]: End with A-roll at Daniel's desk, quick cuts of the project apps and repository, then a final bright-yellow rack hero shot with LEDs and fans running.
