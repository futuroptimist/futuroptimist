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

[NARRATOR]: AI feels like it lives in the cloud, but the cloud is physical.

[VISUAL]: Macro close-ups of the bright-yellow Sugarkube rack: Raspberry Pi LEDs blinking, cooling fans spinning, Ethernet cables entering the PoE+ switch, and a slow tilt revealing all three PLA tiers.

[NARRATOR]: Data centers place concentrated demands on electrical grids; many use water for cooling, and nearby communities can feel those impacts.

[VISUAL]: Licensed stock footage, clearly treated as illustrative, of data-center interiors, electrical substations, cooling equipment, and water infrastructure. Add restrained on-screen labels: "Electricity", "Cooling", "Community impact".

[NARRATOR]: So I built this: Sugarkube, a bright-yellow rack of nine Raspberry Pis hosting my open-source projects.

[VISUAL]: Return to a rack hero shot on the desk. Add a simple label: "Sugarkube: 9 Raspberry Pi 5 nodes".

[NARRATOR]: My goal is modest. I want to see, measure, and control more of the infrastructure behind my software, then find out how much that local control matters.

[VISUAL]: A-roll of Daniel at his desk with the rack visible beside him, then cut to hands plugging in the power meter and opening a terminal dashboard.

[NARRATOR]: I don’t expect this rack to replace the cloud or necessarily beat it on raw efficiency.

[VISUAL]: A-roll holds for the caveat. On-screen text: "Not a universal cloud replacement. Not a watt-for-watt efficiency claim."

> 0:40–1:30: The deployment tax and my SRE motivation

[NARRATOR]: I’ve spent more than a decade building production software, including nearly seven years as a site reliability engineer at YouTube.

[VISUAL]: A-roll of Daniel speaking from the desk. Use a neutral lower-third: "Daniel Smith, software engineer and maker". Do not show private or internal Google or YouTube material.

[NARRATOR]: I’ve been on-call for large-scale, globally distributed systems, so I know reliable services require much more than writing code.

[VISUAL]: A-roll continues, with a simple editor-made checklist beside Daniel: "Packaging", "Deployments", "Verification", "Rollback", "On-call".

[NARRATOR]: My personal projects run at a much smaller scale, but they still need packaging, deployment, verification, updates, and recovery when something fails.

[VISUAL]: Screen recordings of public GitHub repositories, CI checks, sanitized terminal deployment output, verification commands, update logs, and rollback workflow examples. Blur or crop any tokens, private hostnames, or sensitive shell history.

[NARRATOR]: I have way too many passion projects, as you can see on my GitHub, so every one-off deployment path takes time away from improving them.

[VISUAL]: Screen recording of Daniel’s public GitHub profile and repository list, with a subtle highlight jumping between DSPACE, token.place, danielsmith.io, and sugarkube.

[NARRATOR]: Sugarkube is my attempt to make that work boring and repeatable. Boring infrastructure is usually good infrastructure.

[VISUAL]: Terminal montage of repeatable `just` commands and green verification output, then cut back to a calm rack shot with steady LEDs.

> 1:30–3:00: What Sugarkube actually is

[NARRATOR]: Cloud platforms already make small app deployments relatively easy, especially with a trusty LLM whispering in your ear. I wanted a homegrown path built on Kubernetes.

[VISUAL]: A-roll for the motivation, then a simple split-screen: "Cloud path" on one side and "Homegrown Kubernetes path" on the other.

[NARRATOR]: Kubernetes coordinates containerized applications across one or more machines. You describe how an application should run, and Kubernetes places it, restarts it after failures, and rolls out updates.

[VISUAL]: Simple editor-made diagram of containers distributed across one and then multiple machines. Animate labels for "place", "restart after failure", and "rolling update" without overcomplicating the sequence.

[NARRATOR]: Sugarkube runs k3s, a lightweight Kubernetes distribution suited to homelabs and single-board computers. The rack has three bright-yellow PLA tiers, each holding three Raspberry Pi 5s. One unmanaged PoE+ switch provides power and networking.

[VISUAL]: Wide rack footage followed by close-ups of individual Pi 5s, the three printed PLA tiers, the PoE+ switch, Ethernet cables, storage hardware, fans, and office placement.

[NARRATOR]: Only six Pis are active right now. Three form a staging cluster configured for high availability, and three form a separate production cluster configured the same way.

[VISUAL]: Nine-slot rack overlay on real footage: three slots labeled "Staging HA" and three slots labeled "Production HA" in active colors.

[NARRATOR]: A seventh will eventually handle ephemeral development builds without high availability. The last two are still unemployed. I haven’t decided what jobs to give them yet.

[VISUAL]: Continue the nine-slot overlay. Label one slot "Future development node" with a distinct future-plan style, and two slots "Unassigned" with a neutral inactive style.

[NARRATOR]: The repository includes the printable designs, tooling for a Raspberry Pi OS image with cloud-init and k3s preinstalled, and a command layer built around `just`.

[VISUAL]: Screen recording of the Sugarkube repository showing printable design files, image-building tooling, documentation, and the `justfile`.

[NARRATOR]: Its `justfile` packages commands into recipes that bootstrap clusters, onboard applications, deploy and verify them, promote artifacts to production, and roll them back.

[VISUAL]: Sanitized terminal session showing representative `just` commands for bootstrap, deploy, verify, promote, and rollback. Keep secrets, tokens, private hostnames, and sensitive terminal history out of frame.

[NARRATOR]: This makes routine workflows approachable while leaving the manifests, Helm charts, and infrastructure open for inspection and modification.

[VISUAL]: Screen recording through manifests and Helm charts, then a quick editor-made label stack: "Readable", "Repeatable", "Inspectable", "Modifiable".

> 3:00–5:55: The ecosystem running through it

[NARRATOR]: The rack is only interesting if it runs something. Today, Sugarkube is my deployment path for three public projects: DSPACE, token.place, and my portfolio site, danielsmith.io. Watch this list grow over the next few years.

[VISUAL]: Simple diagram connecting Sugarkube to DSPACE, token.place, and danielsmith.io. Add a small label on the open end: "More projects later".

[NARRATOR]: First is DSPACE at democratized.space, a space exploration idle game that, incidentally, hasn’t made it to space yet.

[VISUAL]: Screen recording of the live DSPACE game loading at democratized.space, with the title and main progression UI visible.

[NARRATOR]: My wildly overambitious goal is to turn as much of the space exploration technology tree and its dependencies as I can into something educational and fun.

[VISUAL]: DSPACE quest tree screen recording, slowly panning across unlocked and locked branches.

[NARRATOR]: Its quests span 3D printing, hydroponics, composting, electronics, robotics, astronomy, rocketry, and much more.

[VISUAL]: Representative real footage or screenshots of DSPACE quest content for 3D printing, hydroponics, composting, electronics, robotics, astronomy, and rocketry.

[NARRATOR]: Nearly four years in, I’m nowhere near finished. An explorable 3D version may come much later.

[VISUAL]: A-roll for the caveat. If shown visually, use only a clearly labeled "Future concept: explorable 3D DSPACE" card, not a synthetic mockup.

[NARRATOR]: Second is token.place, my open-source distributed LLM inference platform. Its rate-limited public API currently requires no account, API key, or payment.

[VISUAL]: Screen recording of token.place public API documentation and a safe example request with no private credentials.

[NARRATOR]: Sugarkube hosts the relay, while people contribute spare compute by running models on consumer machines through a desktop app.

[VISUAL]: Screen recording of the desktop compute-node application and a real operator workflow where a node is available for work. Pair with a simple label: "Relay on Sugarkube, compute on volunteered machines".

[NARRATOR]: Requests are end-to-end encrypted between the client and the selected compute node. The relay sees ciphertext and limited routing metadata, but the compute node must decrypt the prompt for inference.

[VISUAL]: Simple custom diagram with three boxes: client, relay, selected compute node. Animate ciphertext passing through the relay, then plaintext becoming available only at the selected compute node.

[NARRATOR]: This changes the trust boundary instead of eliminating trust.

[VISUAL]: A-roll holds for the trust-boundary caveat. On-screen text: "Changed trust boundary, not zero trust.".

[NARRATOR]: Today, more nodes mostly mean more capacity. My long-term hypothesis is that a larger, more diverse pool of independently operated nodes, combined with verifiable work histories and Sybil resistance, could make it harder for a bad actor to dominate node selection.

[VISUAL]: Clearly labeled conceptual diagram: "Future reputation hypothesis". Show diverse independent nodes accumulating verified work histories and a bad actor failing to dominate selection. Do not imply this exists today.

[NARRATOR]: That reputation system does not exist yet.

[VISUAL]: A-roll with on-screen text: "That reputation system does not exist yet.".

[NARRATOR]: By default, the official desktop app keeps prompt and response plaintext in memory and writes only redacted metadata to its logs.

[VISUAL]: Screen recording or documentation view of the desktop app privacy behavior and redacted logs, using safe demo data only.

[NARRATOR]: Compute nodes and relays can both be self-hosted, so the strongest privacy story is running hardware you control.

[VISUAL]: Show token.place repository documentation or real interfaces for self-hosting relay and compute-node options, plus a quick rack close-up for "hardware you control".

[NARRATOR]: Third is danielsmith.io. It deploys as a static site, but that static site packs quite a punch.

[VISUAL]: Screen recording of danielsmith.io loading, with the Three.js house entering frame.

[NARRATOR]: Three.js renders a decorated, lived-in house with two floors and a backyard. You guide an avatar between points of interest representing my projects, experience, and personality. The immersive experience includes a built-in tutorial.

[VISUAL]: Screen recording of avatar movement through both floors, the backyard, project points of interest, and the tutorial prompts.

[NARRATOR]: A dedicated text version serves visitors who prefer a conventional page or use screen readers.

[VISUAL]: Separate screen recording of the dedicated text version, keyboard navigation, headings, links, and readable project sections.

[NARRATOR]: It gives hiring managers and recruiters a memorable first impression while whimsically capturing my interests in graphics programming and game development.

[VISUAL]: A-roll, then quick cuts between the 3D house, project POIs, and code or repo screens for graphics and game-development work.

[NARRATOR]: Together, these projects form a feedback loop. DSPACE uses token.place for its built-in LLM chat NPC, dChat.

[VISUAL]: Screen recording of DSPACE dChat, including the NPC selector and the visible "Powered by token.place" integration where practical.

[NARRATOR]: Sugarkube hosts the relay and deploys all three projects through one staged release workflow. danielsmith.io acts as the front door.

[VISUAL]: Editor-made ecosystem diagram connecting all four projects: Sugarkube deploys the three applications, Sugarkube hosts the token.place relay, token.place powers DSPACE’s dChat, and danielsmith.io serves as the front door.

[NARRATOR]: Each application exposes another weakness in the shared infrastructure, and every fix makes them easier to ship.

[VISUAL]: Animate the feedback loop between application needs and infrastructure improvements, then cut to a successful deployment verification screen.

> 5:55–10:05: Electricity measurement and the efficiency-versus-agency tension

[NARRATOR]: My nine Raspberry Pi 5s each have 8 gigabytes of RAM, but only six are active, and even those are probably overkill for my traffic.

[VISUAL]: Close-ups of Pi 5 boards and labels for "8 GiB RAM" and "6 active nodes" on the nine-slot rack overlay.

[NARRATOR]: I was lucky enough to buy everything before the current Rampocalypse was in full swing.

[VISUAL]: A-roll for the joke, with a quick cut to redacted receipts or the repository BOM. Keep purchase details and personal information obscured.

[NARRATOR]: For a fair comparison, I disconnected the three unused Pis and measured the PoE+ switch, along with any external cooling used during normal operation, through a `<power meter model>`.

[VISUAL]: Real footage of the three unused Pis being disconnected, the PoE+ switch in the measurement boundary, and the continuously running desk fan plugged into the same measured setup. Add boundary labels: "Included: switch, PoE losses, normal cooling, desk fan".

[NARRATOR]: Over `<measurement duration>` during `<representative conditions or workload>`, the setup averaged `<average watts>` watts, peaked at `<peak watts>` watts, and consumed `<measured kilowatt-hours>` kilowatt-hours.

[VISUAL]: Capture the power meter display or logging interface at representative moments. Show the rack idle and during the representative workload. Add measured-value placeholders as on-screen text until final numbers are supplied.

[NARRATOR]: Across an average 730-hour month, that becomes `<monthly kilowatt-hours>` kilowatt-hours. At my marginal electricity rate of `<electricity rate>` per kilowatt-hour, it costs `<monthly electricity cost>` per month, or `<annual electricity cost>` per year.

[VISUAL]: Simple calculation graphic: watts to monthly kilowatt-hours to monthly and annual cost, preserving placeholders for Daniel’s final values.

[NARRATOR]: That includes the switch, PoE losses, and cooling used during the test. It excludes my shared router and modem, along with token.place compute nodes outside the rack. A separate GPU-enabled computer needs its own measurement.

[VISUAL]: Measurement-boundary diagram. Included items are the rack, PoE+ switch, PoE losses, normal cooling, and desk fan. Excluded items are the router, modem, off-rack token.place compute nodes, and separate GPU computer.

[NARRATOR]: For the cloud comparison, I modeled self-managed three-node staging and production clusters in one availability zone in AWS’s Oregon region.

[VISUAL]: Screen recording of the AWS calculator or a clean editor-made architecture diagram labeled "Oregon, one availability zone" with two self-managed three-node k3s clusters.

[NARRATOR]: The single availability zone mirrors the rack’s single-site failure domain.

[VISUAL]: A-roll for the comparison caveat, with a simple side-by-side: "Rack: one site" and "AWS model: one AZ".

[NARRATOR]: The model uses six on-demand Linux `c7g.xlarge` instances. Their four Arm vCPUs and 8 GiB of memory roughly match each Pi’s resource shape, although the AWS instances are substantially faster.

[VISUAL]: Architecture diagram or calculator view showing six `c7g.xlarge` instances. Add concise labels: "4 Arm vCPUs", "8 GiB memory", "Substantially faster than Pi 5".

[NARRATOR]: Each instance gets a 256 GiB gp3 volume and a public IPv4 address. I kept k3s and Cloudflare Tunnel, excluding EKS, a managed load balancer, a NAT gateway, RDS, and managed observability.

[VISUAL]: Diagram expands to six 256 GiB gp3 volumes and six public IPv4 addresses. Add an exclusions list: "No EKS, managed load balancer, NAT gateway, RDS, managed observability".

[NARRATOR]: Using AWS’s public rates from July 22, 2026, compute costs $635.10 per month, storage costs $122.88, and IPv4 addresses cost $21.90. The fixed total is $779.88 per month, or $9,358.56 per year, before taxes, data transfer, snapshots, expanded monitoring, backups, or support.

[VISUAL]: Readable table or animated cost stack labeled "Pricing snapshot: July 22, 2026". Rows: compute $635.10, storage $122.88, IPv4 $21.90, total $779.88 per month, $9,358.56 per year. Add concise exclusions below.

[NARRATOR]: Discounts, smaller instances, or shutting staging down could lower that bill substantially, but would change this always-on, shape-matched comparison.

[VISUAL]: A-roll for the caveat. On-screen text: "Discounts, smaller instances, or stopping staging change the model.".

[NARRATOR]: AWS does not publish the direct power consumption of an individual instance, so this compares cost rather than watts.

[VISUAL]: A-roll continues. On-screen text: "Financial comparison, not direct energy measurement.".

[NARRATOR]: Its newer hardware and data-center economies may win on performance per watt, but this experiment did not prove that.

[VISUAL]: Illustrative licensed stock data-center footage beside a rack shot, clearly labeled "Performance-per-watt not measured here".

[NARRATOR]: The full nine-node build cost me `<full nine-node BOM total>`. Excluding the three unused Pi node kits while retaining required shared equipment brought the comparable six-node cost to `<comparable six-node BOM total>`. The repository supplied the quantities; my receipts supplied the prices.

[VISUAL]: Real hardware, printed parts, cabling, redacted receipts, and the repository BOM. Create a simple comparison card for "Full nine-node total" and "Comparable six-node total" using placeholders.

[NARRATOR]: If local electricity costs less than $779.88 per month, simple cash break-even occurs after `<break-even months>` months.

[VISUAL]: Cumulative-cost line chart with placeholders, showing local upfront cost plus electricity crossing the AWS monthly line at the break-even month.

[NARRATOR]: That is the comparable six-node cost divided by the monthly savings over AWS, rounded up.

[VISUAL]: Show the formula: `comparable six-node cost / (AWS monthly cost - local monthly electricity cost)`.

[NARRATOR]: If local operating costs equal or exceed AWS, there is no positive break-even under these assumptions.

[VISUAL]: Add a no-break-even case to the chart, with the local operating line never crossing below AWS savings.

[NARRATOR]: This calculation also ignores my labor, failures, replacement parts, internet service, AWS discounts, and the value of managed infrastructure.

[VISUAL]: A-roll for limitations, with a short on-screen exclusions list.

[NARRATOR]: A real lifecycle comparison would need to include manufacturing, shipping, embodied energy, and indirect water use on both sides.

[VISUAL]: A-roll continues, then illustrative shots of hardware shipping boxes, the local rack, and licensed stock data-center water and power infrastructure. Avoid implying either side has zero indirect water use.

[NARRATOR]: The rack itself uses no cooling water, unless you count what I drank while assembling it.

[VISUAL]: Real shot of Daniel taking a drink of water at the desk next to the rack.

[NARRATOR]: There is no dedicated air conditioning, humidity control, or liquid cooling; just onboard fans and a desk fan.

[VISUAL]: Close-ups of onboard fans and the continuously running desk fan. Add label: "Normal cooling during measurement".

[NARRATOR]: Running locally gives me more agency over energy use. I can meter the rack, choose its electricity source, schedule work around solar generation, power down unused environments, and own the means of production for this tiny corner of the internet.

[VISUAL]: Montage of the power meter, rack controls, deployment schedules, environments being powered down, and licensed stock footage of solar panels, battery, and inverter labeled "Future off-grid plan" where applicable.

[NARRATOR]: That control matters to me, even though it does not automatically make the homelab greener.

[VISUAL]: A-roll for the nuanced environmental conclusion. On-screen text: "Agency is not the same as automatic sustainability.".

> 10:05–11:15: Participation and concluding vision

[NARRATOR]: All four projects are open source. You can play DSPACE and suggest quests, explore danielsmith.io, run a token.place compute node or relay, or try Sugarkube on your own Raspberry Pis.

[VISUAL]: Screen recording montage of each public project: DSPACE gameplay and quest suggestions, danielsmith.io, token.place compute node or relay docs, and Sugarkube setup docs.

[NARRATOR]: Even testing the documentation and telling me where it breaks would help.

[VISUAL]: GitHub issues or discussion page with a safe example issue title like "Docs feedback", plus A-roll nodding to the camera.

[NARRATOR]: Very few people need a micro data center at home. You can start with one Pi or an old computer.

[VISUAL]: A-roll, then simple practical shots of a single Raspberry Pi and an old desktop or mini PC.

[NARRATOR]: This yellow rack isn’t going to defeat AWS in single combat.

[VISUAL]: A-roll for the joke, with a playful but simple side-by-side of the rack and an AWS architecture icon labeled "Not a duel".

[NARRATOR]: I want Sugarkube to provide another option where people can own more of the stack, learn Kubernetes by running something real, and decide how their hardware and energy are used.

[VISUAL]: Rack hero shot, terminal deployment, Kubernetes diagram, and power meter in a calm sequence.

[NARRATOR]: Long term, I plan to run Sugarkube from a dedicated off-grid solar, battery, and inverter system. Subscribe if you want to see that process!

[VISUAL]: Real or licensed stock footage of solar panels, batteries, and an inverter, clearly labeled "Future plan: dedicated off-grid power". Pair the subscription call to action with restrained on-screen text: "Subscribe for the off-grid build".

[NARRATOR]: I started Sugarkube because deploying my projects kept getting in the way of building them.

[VISUAL]: A-roll, then cut to a sanitized terminal deployment completing successfully.

[NARRATOR]: Now they form one connected ecosystem, and the infrastructure is helping me move faster.

[VISUAL]: Return to the four-project ecosystem diagram and animate the feedback loop one final time.

[NARRATOR]: It’s visible, measurable, modifiable, and mine.

[VISUAL]: Final sequence: power meter, open repository, application demos, and a closing hero shot of the bright-yellow rack with LEDs and fans running.
