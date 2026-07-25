# Sugarkube (working title) (2026-09-01)

> Draft script for video `<youtube_id>`

## Outline

- 0:00–0:40: physical hook, environmental concern, and honest thesis
- 0:40–1:30: deployment tax and SRE motivation
- 1:30–3:30: Sugarkube hardware, k3s platform, and command layer
- 3:30–6:25: DSPACE, token.place, and danielsmith.io as a connected ecosystem
- 6:25–10:35: measured electricity, AWS cost comparison, and the efficiency-versus-agency tension
- 10:35–11:45: participation and concluding vision

## Script

### 0:00–0:40: Physical hook, environmental concern, and honest thesis

[NARRATOR]: AI feels like it lives in the cloud, but the cloud is physical.

[NARRATOR]: Data centers place concentrated demands on electrical grids; many use water for cooling, and nearby communities can feel those impacts.

[VISUAL]: Open on macro close-ups of the bright-yellow Sugarkube rack: LEDs blinking, fan blades spinning, Ethernet cables, PoE+ switch ports, and all three printed tiers. Cut to appropriately licensed stock footage of data-center interiors, electrical rooms, cooling equipment, and water infrastructure labeled "Illustrative cloud infrastructure footage."

[NARRATOR]: So I built this: Sugarkube, a bright-yellow rack of nine Raspberry Pis hosting my open-source projects.

[VISUAL]: Return to a clean rack hero shot on Daniel's desk or shelf. Add a restrained lower-third: "Sugarkube: 9 Raspberry Pi 5 nodes."

[NARRATOR]: My goal is modest.

[NARRATOR]: I want to see, measure, and control more of the infrastructure behind my software, then find out how much that local control matters.

[NARRATOR]: I don’t expect this rack to replace the cloud or necessarily beat it on raw efficiency.

[VISUAL]: A-roll of Daniel at his desk with the rack visible nearby. Brief insert of a hand placing a power meter in frame, then back to A-roll for the caveat.

### 0:40–1:30: The deployment tax and my SRE motivation

[NARRATOR]: I’ve spent more than a decade building production software, including nearly seven years as a site reliability engineer at YouTube.

[NARRATOR]: I’ve been on-call for large-scale, globally distributed systems, so I know reliable services require much more than writing code.

[VISUAL]: A-roll. Use a simple on-screen label for experience only, without showing private or internal Google or YouTube material.

[NARRATOR]: My personal projects run at a much smaller scale, but they still need packaging, deployment, verification, updates, and recovery when something fails.

[VISUAL]: Screen recordings of public GitHub repositories, CI status checks, terminal deployment commands, verification output, update logs, and rollback commands. Blur or crop any secrets, tokens, private hostnames, or sensitive terminal history.

[NARRATOR]: I have way too many passion projects, as you can see on my GitHub, so every one-off deployment path takes time away from improving them.

[NARRATOR]: Sugarkube is my attempt to make that work boring and repeatable.

[NARRATOR]: Boring infrastructure is usually good infrastructure.

[VISUAL]: Screen recording scrolling Daniel's public GitHub project list, then cut to a tidy terminal menu or `just --list` output. End with A-roll for the joke and thesis.

### 1:30–3:30: What Sugarkube actually is

[NARRATOR]: Cloud platforms already make small app deployments relatively easy, especially with a trusty LLM whispering in your ear.

[NARRATOR]: Full disclosure: this is not artisanal, farm-to-table software.

[NARRATOR]: I use agentic coding across all four projects.

[NARRATOR]: I know.

[VISUAL]: Stay on A-roll as Daniel says the disclosure, then cut on "I know" to a very brief, appropriately sourced Alexis Rose "Ew, David!" reaction clip from Schitt's Creek before returning to Daniel. If that clip cannot be sourced appropriately for the edit, Daniel should record his own quick reaction instead of using AI-generated media.

[NARRATOR]: I get the skepticism.

[NARRATOR]: For one person maintaining an ecosystem this overambitious, though, coding agents are often the difference between an idea staying in my notes and becoming working software.

[NARRATOR]: I still make the architectural decisions, verify the results, and take responsibility when something breaks.

[VISUAL]: A-roll plus a sanitized screen recording of a real agentic-coding workflow, such as reviewing a proposed diff, inspecting tests, or verifying a change. Do not expose secrets, tokens, private hostnames, or sensitive terminal history.

[NARRATOR]: I wanted a homegrown path built on Kubernetes.

[VISUAL]: Transition from A-roll back to the bright-yellow rack, then into the Kubernetes explanation with a simple two-column title card: "Managed cloud convenience" vs "Homegrown Kubernetes path."

[NARRATOR]: Kubernetes coordinates containerized applications across one or more machines.

[NARRATOR]: You describe how an application should run, and Kubernetes places it, restarts it after failures, and rolls out updates.

[VISUAL]: Editor-made diagram showing containers distributed across one machine, then several machines. Label placement, restart after failure, and rolling update steps with simple arrows.

[NARRATOR]: Sugarkube runs k3s, a lightweight Kubernetes distribution suited to homelabs and single-board computers.

[NARRATOR]: The rack has three bright-yellow PLA tiers, each holding three Raspberry Pi 5s.

[NARRATOR]: One unmanaged PoE+ switch provides power and networking.

[VISUAL]: Wide shot and close-ups of the full rack, individual Pi 5 boards, three PLA tiers, the PoE+ switch, Ethernet cables, storage hardware, onboard fans, desk fan, and office placement.

[NARRATOR]: Only six Pis are active right now.

[NARRATOR]: Three form a staging cluster configured for high availability, and three form a separate production cluster configured the same way.

[NARRATOR]: A seventh will eventually handle ephemeral development builds without high availability.

[NARRATOR]: The last two are still unemployed.

[NARRATOR]: I haven’t decided what jobs to give them yet.

[VISUAL]: Overlay a nine-slot rack diagram on the real rack: three active staging nodes, three active production nodes, one planned development node styled as future, and two unassigned nodes styled distinctly as unused. Keep active, future, and unassigned states visually different.

[NARRATOR]: The repository includes the printable designs, tooling for a Raspberry Pi OS image with cloud-init and k3s preinstalled, and a command layer built around `just`.

[NARRATOR]: Its `justfile` packages commands into recipes that bootstrap clusters, onboard applications, deploy and verify them, promote artifacts to production, and roll them back.

[NARRATOR]: This makes routine workflows approachable while leaving the manifests, Helm charts, and infrastructure open for inspection and modification.

[VISUAL]: Screen recordings of the Sugarkube repository showing printable design files, image-building tooling, `justfile`, manifests, Helm charts, and documentation. Show representative sanitized `just` commands for bootstrap, deploy, verify, promote, and rollback.

### 3:30–6:25: The ecosystem running through it

[NARRATOR]: The rack is only interesting if it runs something.

[NARRATOR]: Today, Sugarkube is my deployment path for three public projects: DSPACE, token.place, and my portfolio site, danielsmith.io.

[NARRATOR]: Watch this list grow over the next few years.

[VISUAL]: Simple editor-made ecosystem diagram with Sugarkube at the center and three current deployed projects around it. Add a small "future projects" placeholder clearly labeled as future.

[NARRATOR]: First is DSPACE at democratized.space, a space exploration idle game that, incidentally, hasn’t made it to space yet.

[NARRATOR]: My wildly overambitious goal is to turn as much of the space exploration technology tree and its dependencies as I can into something educational and fun.

[VISUAL]: Screen recording of the live DSPACE game landing page and core gameplay. Include A-roll or a small comedic cutaway on "hasn’t made it to space yet."

[NARRATOR]: Its quests span 3D printing, hydroponics, composting, electronics, robotics, astronomy, rocketry, and much more.

[NARRATOR]: Nearly four years in, I’m nowhere near finished.

[NARRATOR]: An explorable 3D version may come much later.

[VISUAL]: Show DSPACE quest trees and representative real footage or screenshots for 3D printing, hydroponics, composting, electronics, robotics, astronomy, and rocketry. Use A-roll for the unfinished caveat and label any 3D-version reference as "Future concept, not implemented."

[NARRATOR]: Second is token.place, my open-source distributed LLM inference platform.

[NARRATOR]: Its rate-limited public API currently requires no account, API key, or payment.

[NARRATOR]: Sugarkube hosts the relay, while people contribute spare compute by running models on consumer machines through a desktop app.

[VISUAL]: Screen recording of the token.place public API documentation or demo, the desktop compute-node application, and a real operator workflow. Add a label: "Sugarkube hosts relay. Operators run compute nodes."

[NARRATOR]: Requests are end-to-end encrypted between the client and the selected compute node.

[NARRATOR]: The relay sees ciphertext and limited routing metadata, but the compute node must decrypt the prompt for inference.

[NARRATOR]: This changes the trust boundary instead of eliminating trust.

[VISUAL]: Simple custom diagram with client, relay, and selected compute node. Animate ciphertext passing through the relay and plaintext appearing only at the selected compute node. Cut to A-roll for "changes the trust boundary instead of eliminating trust."

[NARRATOR]: Today, more nodes mostly mean more capacity.

[NARRATOR]: My long-term hypothesis is that a larger, more diverse pool of independently operated nodes, combined with verifiable work histories and Sybil resistance, could make it harder for a bad actor to dominate node selection.

[NARRATOR]: That reputation system does not exist yet.

[VISUAL]: A-roll with on-screen text: "That reputation system does not exist yet." Use a clearly labeled conceptual diagram, "Future hypothesis," showing diverse independent nodes accumulating verified work histories. Do not present it as current functionality.

[NARRATOR]: By default, the official desktop app keeps prompt and response plaintext in memory and writes only redacted metadata to its logs.

[NARRATOR]: Compute nodes and relays can both be self-hosted, so the strongest privacy story is running hardware you control.

[VISUAL]: A-roll for the privacy caveat. Insert real repository documentation or settings screens for self-hosted relay and compute-node options where public interfaces exist. Keep logs sanitized and show redaction labels.

[NARRATOR]: Third is danielsmith.io.

[NARRATOR]: It deploys as a static site, but that static site packs quite a punch.

[NARRATOR]: Three.js renders a decorated, lived-in house with two floors and a backyard.

[NARRATOR]: You guide an avatar between points of interest representing my projects, experience, and personality.

[NARRATOR]: The immersive experience includes a built-in tutorial.

[VISUAL]: Screen recording of danielsmith.io showing the Three.js house, avatar movement, both floors, backyard, project points of interest, and tutorial prompts.

[NARRATOR]: A dedicated text version serves visitors who prefer a conventional page or use screen readers.

[NARRATOR]: It gives hiring managers and recruiters a memorable first impression while whimsically capturing my interests in graphics programming and game development.

[VISUAL]: Separate screen recording of the dedicated text version, keyboard navigation, conventional sections, and accessibility-focused layout. Avoid implying a screen reader endorsement unless actually tested.

[NARRATOR]: Together, these projects form a feedback loop.

[NARRATOR]: DSPACE uses token.place for its built-in LLM chat NPC, dChat.

[NARRATOR]: Sugarkube hosts the relay and deploys all three projects through one staged release workflow.

[NARRATOR]: danielsmith.io acts as the front door.

[NARRATOR]: Each application exposes another weakness in the shared infrastructure, and every fix makes them easier to ship.

[VISUAL]: Editor-made connected ecosystem diagram: Sugarkube deploys DSPACE, token.place, and danielsmith.io; Sugarkube hosts the token.place relay; token.place powers DSPACE dChat; danielsmith.io is the front door. Animate a feedback loop from application needs back to infrastructure improvements. Include a brief DSPACE dChat and NPC selector screen recording with visible "Powered by token.place" integration where practical.

### 6:25–10:35: Electricity measurement and the efficiency-versus-agency tension

[NARRATOR]: My nine Raspberry Pi 5s each have 8 gigabytes of RAM, but only six are active, and even those are probably overkill for my traffic.

[NARRATOR]: I was lucky enough to buy everything before the current Rampocalypse was in full swing.

[VISUAL]: Close-up lineup of Pi 5 boards and RAM labels, then the nine-slot overlay again with only six active nodes highlighted. Use A-roll for the Rampocalypse joke.

[NARRATOR]: For a fair comparison, I disconnected the three unused Pis and measured the PoE+ switch, along with any external cooling used during normal operation, through a `<power meter model>`.

[NARRATOR]: Over `<measurement duration>` during `<representative conditions or workload>`, the setup averaged `<average watts>` watts, peaked at `<peak watts>` watts, and consumed `<measured kilowatt-hours>` kilowatt-hours.

[VISUAL]: Show the three unused Pis being disconnected, then the PoE+ switch and continuously running desk fan connected inside the measurement boundary. Capture the power meter display or logging interface at representative idle and workload moments. Add measured values as on-screen text placeholders matching the narration until final numbers are supplied.

[NARRATOR]: Across an average 730-hour month, that becomes `<monthly kilowatt-hours>` kilowatt-hours.

[NARRATOR]: At my marginal electricity rate of `<electricity rate>` per kilowatt-hour, it costs `<monthly electricity cost>` per month, or `<annual electricity cost>` per year.

[VISUAL]: Simple calculator-style graphic: watts to monthly kWh to monthly and annual cost. Keep placeholders visible and clearly marked "final measured values pending."

[NARRATOR]: That includes the switch, PoE losses, and cooling used during the test.

[NARRATOR]: It excludes my shared router and modem, along with token.place compute nodes outside the rack.

[NARRATOR]: A separate GPU-enabled computer needs its own measurement.

[VISUAL]: Boundary diagram around the rack, PoE+ switch, cabling, and continuously running desk fan. Put router, modem, off-rack token.place compute nodes, and separate GPU computer outside the boundary with "excluded" labels.

[NARRATOR]: For the cloud comparison, I modeled self-managed three-node staging and production clusters in one availability zone in AWS’s Oregon region.

[NARRATOR]: The single availability zone mirrors the rack’s single-site failure domain.

[VISUAL]: Screen recording of the AWS calculator or a clean editor-made architecture diagram showing two self-managed three-node k3s clusters in one Oregon availability zone. Label the single-site failure domain.

[NARRATOR]: The model uses six on-demand Linux `c7g.xlarge` instances.

[NARRATOR]: Their four Arm vCPUs and 8 GiB of memory roughly match each Pi’s resource shape, although the AWS instances are substantially faster.

[VISUAL]: Architecture card showing six `c7g.xlarge` instances with labels: "4 Arm vCPU" and "8 GiB memory." Add a qualification label: "Shape-matched, not performance-matched."

[NARRATOR]: Each instance gets a 256 GiB gp3 volume and a public IPv4 address.

[NARRATOR]: I kept k3s and Cloudflare Tunnel, excluding EKS, a managed load balancer, a NAT gateway, RDS, and managed observability.

[VISUAL]: Add six 256 GiB gp3 volumes and six public IPv4 addresses to the AWS diagram. Include an on-screen exclusions list: EKS, managed load balancer, NAT gateway, RDS, managed observability.

[NARRATOR]: Using AWS’s public rates from July 22, 2026, compute costs $635.10 per month, storage costs $122.88, and IPv4 addresses cost $21.90.

[NARRATOR]: The fixed total is $779.88 per month, or $9,358.56 per year, before taxes, data transfer, snapshots, expanded monitoring, backups, or support.

[VISUAL]: Readable table or animated stack labeled "AWS pricing snapshot: July 22, 2026." Rows: compute $635.10, storage $122.88, IPv4 $21.90, total $779.88/month and $9,358.56/year. Add concise exclusions: taxes, data transfer, snapshots, expanded monitoring, backups, support.

[NARRATOR]: Discounts, smaller instances, or shutting staging down could lower that bill substantially, but would change this always-on, shape-matched comparison.

[VISUAL]: A-roll for the caveat with on-screen text: "Always-on, shape-matched comparison."

[NARRATOR]: AWS does not publish the direct power consumption of an individual instance, so this compares cost rather than watts.

[NARRATOR]: Its newer hardware and data-center economies may win on performance per watt, but this experiment did not prove that.

[VISUAL]: A-roll. Add two simple labels: "Financial comparison" and "Not a watt-for-watt energy comparison."

[NARRATOR]: The full nine-node build cost me `<full nine-node BOM total>`.

[NARRATOR]: Excluding the three unused Pi node kits while retaining required shared equipment brought the comparable six-node cost to `<comparable six-node BOM total>`.

[NARRATOR]: The repository supplied the quantities; my receipts supplied the prices.

[VISUAL]: Show real hardware, printed parts, cabling, redacted receipts, and the repository BOM. Create a simple comparison card for full nine-node total versus comparable six-node total, keeping placeholders until Daniel supplies final numbers.

[NARRATOR]: If local electricity costs less than $779.88 per month, simple cash break-even occurs after `<break-even months>` months.

[NARRATOR]: That is the comparable six-node cost divided by the monthly savings over AWS, rounded up.

[NARRATOR]: If local operating costs equal or exceed AWS, there is no positive break-even under these assumptions.

[VISUAL]: Show the formula: `comparable six-node cost / (AWS monthly cost - local monthly electricity cost)`. Optionally add a cumulative-cost line chart with the crossing point at the break-even month, plus a clear "No positive break-even" case when local monthly operating cost is greater than or equal to AWS.

[NARRATOR]: This calculation also ignores my labor, failures, replacement parts, internet service, AWS discounts, and the value of managed infrastructure.

[NARRATOR]: A real lifecycle comparison would need to include manufacturing, shipping, embodied energy, and indirect water use on both sides.

[VISUAL]: A-roll for lifecycle limitations. Add a concise on-screen list of ignored factors without implying either side has zero indirect impact.

[NARRATOR]: The rack itself uses no cooling water, unless you count what I drank while assembling it.

[NARRATOR]: There is no dedicated air conditioning, humidity control, or liquid cooling; just onboard fans and a desk fan.

[VISUAL]: Real shot of Daniel taking a drink for the joke, then close-ups of onboard fans and the continuously running desk fan. Avoid suggesting there is no indirect water use from electricity or manufacturing.

[NARRATOR]: Running locally gives me more agency over energy use.

[NARRATOR]: I can meter the rack, choose its electricity source, schedule work around solar generation, power down unused environments, and own the means of production for this tiny corner of the internet.

[NARRATOR]: That control matters to me, even though it does not automatically make the homelab greener.

[VISUAL]: Show the power meter, rack controls, terminal commands powering down or scaling environments, and deployment dashboards. Use licensed stock or real footage of solar panels, battery, and inverter only with a label: "Future off-grid goal."

### 10:35–11:45: Participation and concluding vision

[NARRATOR]: All four projects are open source.

[NARRATOR]: You can play DSPACE and suggest quests, explore danielsmith.io, run a token.place compute node or relay, or try Sugarkube on your own Raspberry Pis.

[NARRATOR]: Even testing the documentation and telling me where it breaks would help.

[VISUAL]: Screen montage of the four public repositories and apps: DSPACE gameplay and quest feedback path, danielsmith.io, token.place compute node or relay docs, and Sugarkube setup docs. Use restrained lower-thirds for each action.

[NARRATOR]: Very few people need a micro data center at home.

[NARRATOR]: You can start with one Pi or an old computer.

[NARRATOR]: This yellow rack isn’t going to defeat AWS in single combat.

[NARRATOR]: I want Sugarkube to provide another option where people can own more of the stack, learn Kubernetes by running something real, and decide how their hardware and energy are used.

[VISUAL]: A-roll for the caveat, then practical shots of one Raspberry Pi, an old computer, the full yellow rack, and a simple Kubernetes learning diagram.

[NARRATOR]: Long term, I plan to run Sugarkube from a dedicated off-grid solar, battery, and inverter system.

[NARRATOR]: Subscribe if you want to see that process!

[VISUAL]: Real or appropriately licensed stock footage of solar panels, battery, and inverter hardware labeled "Future plan." Pair the subscribe call to action with restrained on-screen text.

[NARRATOR]: I started Sugarkube because deploying my projects kept getting in the way of building them.

[NARRATOR]: Now they form one connected ecosystem, and the infrastructure is helping me move faster.

[NARRATOR]: It’s visible, measurable, modifiable, and mine.

[VISUAL]: End with A-roll, quick shots of Sugarkube deployments and the three applications, the connected ecosystem diagram resolving cleanly, and a final bright-yellow rack hero shot with LEDs and fans running.
