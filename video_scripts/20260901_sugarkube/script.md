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

[VISUAL]: Macro close-ups of the bright-yellow Sugarkube rack: Pi LEDs blinking, cooling fans spinning, Ethernet cables, PoE+ switch ports, and all three PLA tiers in quick succession.

[NARRATOR]: Data centers place concentrated demands on electrical grids; many use water for cooling, and nearby communities can feel those impacts.

[VISUAL]: Licensed stock footage, clearly illustrative, of data-center aisles, electrical substations, cooling equipment, and water infrastructure. Add restrained labels: "Electricity", "Cooling", "Local impacts".

[NARRATOR]: So I built this: Sugarkube, a bright-yellow rack of nine Raspberry Pis hosting my open-source projects.

[VISUAL]: Return to a rack hero shot on Daniel's desk or office shelf. Slow push-in with on-screen label: "Sugarkube: 9 Raspberry Pi 5s".

[NARRATOR]: My goal is modest. I want to see, measure, and control more of the infrastructure behind my software, then find out how much that local control matters.

[VISUAL]: A-roll of Daniel at his desk with the rack visible beside him, then cut to a hand plugging in the power meter and opening a terminal dashboard.

[NARRATOR]: I don’t expect this rack to replace the cloud or necessarily beat it on raw efficiency.

[VISUAL]: A-roll for the caveat. Add small on-screen text: "Control experiment, not a universal efficiency claim".

> 0:40–1:30: The deployment tax and my SRE motivation

[NARRATOR]: I’ve spent more than a decade building production software, including nearly seven years as a site reliability engineer at YouTube.

[VISUAL]: A-roll of Daniel speaking from his desk. Use a simple lower-third: "Daniel Smith | Software engineer and SRE". Do not show private or internal Google or YouTube material.

[NARRATOR]: I’ve been on-call for large-scale, globally distributed systems, so I know reliable services require much more than writing code.

[VISUAL]: A-roll continues, with a simple editor-made checklist appearing beside Daniel: "Monitoring", "Rollouts", "Recovery", "Verification".

[NARRATOR]: My personal projects run at a much smaller scale, but they still need packaging, deployment, verification, updates, and recovery when something fails.

[VISUAL]: Screen recording montage of public GitHub repositories, CI runs, terminal deployment commands, verification output, update logs, and rollback workflow examples. Blur or crop secrets, tokens, private hostnames, and terminal history.

[NARRATOR]: I have way too many passion projects, as you can see on my GitHub, so every one-off deployment path takes time away from improving them.

[VISUAL]: Screen recording of Daniel's public GitHub profile and repository list, then a simple timer graphic labeled "deployment tax" stealing time from "building features".

[NARRATOR]: Sugarkube is my attempt to make that work boring and repeatable. Boring infrastructure is usually good infrastructure.

[VISUAL]: Terminal screen recording of a repeatable `just` workflow finishing successfully, followed by an A-roll smile or shrug on "Boring infrastructure".

> 1:30–3:00: What Sugarkube actually is

[NARRATOR]: Cloud platforms already make small app deployments relatively easy, especially with a trusty LLM whispering in your ear. I wanted a homegrown path built on Kubernetes.

[VISUAL]: A-roll for the motivation. Brief cutaway to a generic cloud deployment UI, then back to the local rack and a Kubernetes logo or label.

[NARRATOR]: Kubernetes coordinates containerized applications across one or more machines.

[VISUAL]: Simple editor-made diagram: container boxes distributed across one machine, then across multiple machines labeled "node 1", "node 2", and "node 3".

[NARRATOR]: You describe how an application should run, and Kubernetes places it, restarts it after failures, and rolls out updates.

[VISUAL]: Continue the diagram with three labeled beats: placement, restart after a node failure, and rolling update from version A to version B.

[NARRATOR]: Sugarkube runs k3s, a lightweight Kubernetes distribution suited to homelabs and single-board computers.

[VISUAL]: Screen recording of k3s documentation or public repo, then terminal output from a safe `kubectl get nodes` style view with sensitive names redacted if needed.

[NARRATOR]: The rack has three bright-yellow PLA tiers, each holding three Raspberry Pi 5s. One unmanaged PoE+ switch provides power and networking.

[VISUAL]: Wide rack shot, then close-ups of individual Pi 5s, the three printed PLA tiers, PoE+ switch, Ethernet cables, storage hardware, cooling fans, and rack placement in the office.

[NARRATOR]: Only six Pis are active right now. Three form a staging cluster configured for high availability, and three form a separate production cluster configured the same way.

[VISUAL]: Nine-slot rack overlay on real footage: three active staging nodes in one color and three active production nodes in another. Label both "HA cluster".

[NARRATOR]: A seventh will eventually handle ephemeral development builds without high availability.

[VISUAL]: Same nine-slot overlay. Highlight the seventh slot with a distinct dashed style labeled "planned development node" and "future".

[NARRATOR]: The last two are still unemployed. I haven’t decided what jobs to give them yet.

[VISUAL]: Highlight the remaining two slots in gray labeled "unassigned". Optional light joke with tiny "job opening" labels, but keep it clearly informational.

[NARRATOR]: The repository includes the printable designs, tooling for a Raspberry Pi OS image with cloud-init and k3s preinstalled, and a command layer built around `just`.

[VISUAL]: Screen recording through the Sugarkube repository: printable designs, image-building tooling, cloud-init files, k3s setup, and the `justfile`.

[NARRATOR]: Its `justfile` packages commands into recipes that bootstrap clusters, onboard applications, deploy and verify them, promote artifacts to production, and roll them back.

[VISUAL]: Terminal capture showing representative `just` commands for bootstrap, deploy, verify, promote, and rollback. Use demo-safe output and avoid exposing secrets, tokens, private hostnames, or sensitive shell history.

[NARRATOR]: This makes routine workflows approachable while leaving the manifests, Helm charts, and infrastructure open for inspection and modification.

[VISUAL]: Screen recording of manifests, Helm charts, and documentation side by side with a concise on-screen note: "Readable, inspectable, modifiable".

> 3:00–5:55: The ecosystem running through it

[NARRATOR]: The rack is only interesting if it runs something.

[VISUAL]: Rack hero shot transitions into a simple editor-made diagram with an empty center labeled "Sugarkube".

[NARRATOR]: Today, Sugarkube is my deployment path for three public projects: DSPACE, token.place, and my portfolio site, danielsmith.io.

[VISUAL]: Add the three project logos or page screenshots around Sugarkube in the diagram, connected by deployment arrows.

[NARRATOR]: Watch this list grow over the next few years.

[VISUAL]: A-roll with a small on-screen label: "Future projects will be added as they are real".

[NARRATOR]: First is DSPACE at democratized.space, a space exploration idle game that, incidentally, hasn’t made it to space yet.

[VISUAL]: Screen recording of the live DSPACE game at democratized.space, opening on the main interface and quest tree. Add a playful on-screen note: "Still Earth-based".

[NARRATOR]: My wildly overambitious goal is to turn as much of the space exploration technology tree and its dependencies as I can into something educational and fun.

[VISUAL]: Pan through DSPACE quest trees and educational content pages, emphasizing dependency chains and progression.

[NARRATOR]: Its quests span 3D printing, hydroponics, composting, electronics, robotics, astronomy, rocketry, and much more.

[VISUAL]: Fast but readable montage of representative DSPACE quests and real project footage or photos: 3D prints, hydroponic baskets, compost setup, electronics bench, robotics parts, telescope or astronomy imagery, and rocketry references.

[NARRATOR]: Nearly four years in, I’m nowhere near finished.

[VISUAL]: A-roll for the self-aware caveat, with the DSPACE backlog or quest tree visible on a monitor behind Daniel if practical.

[NARRATOR]: An explorable 3D version may come much later.

[VISUAL]: A-roll continues or show a clearly labeled "future concept" card. Do not create synthetic mockups that could be mistaken for existing gameplay.

[NARRATOR]: Second is token.place, my open-source distributed LLM inference platform.

[VISUAL]: Screen recording of token.place public site or repository, then the desktop compute-node application opening to a real operator workflow.

[NARRATOR]: Its rate-limited public API currently requires no account, API key, or payment.

[VISUAL]: Screen recording of public API documentation or a safe demo request. Add on-screen text: "Rate-limited public API" and "No account, API key, or payment currently required".

[NARRATOR]: Sugarkube hosts the relay, while people contribute spare compute by running models on consumer machines through a desktop app.

[VISUAL]: Simple diagram: client sends request to Sugarkube-hosted relay, relay routes to a selected desktop compute node. Cut to the desktop app showing a real node workflow.

[NARRATOR]: Requests are end-to-end encrypted between the client and the selected compute node.

[VISUAL]: Animate ciphertext packets passing from client through relay to compute node in the custom diagram.

[NARRATOR]: The relay sees ciphertext and limited routing metadata, but the compute node must decrypt the prompt for inference.

[VISUAL]: Diagram zoom: relay remains locked and labeled "ciphertext + routing metadata" while the selected compute node unlocks plaintext for inference.

[NARRATOR]: This changes the trust boundary instead of eliminating trust.

[VISUAL]: A-roll for the trust caveat. Add small on-screen text: "Trust boundary changes, it does not disappear".

[NARRATOR]: Today, more nodes mostly mean more capacity.

[VISUAL]: Diagram adds extra compute nodes and a capacity meter increasing, labeled "current behavior".

[NARRATOR]: My long-term hypothesis is that a larger, more diverse pool of independently operated nodes, combined with verifiable work histories and Sybil resistance, could make it harder for a bad actor to dominate node selection.

[VISUAL]: Clearly labeled conceptual diagram: diverse independent nodes accumulate verified work histories while a "future reputation / Sybil resistance hypothesis" label stays on screen.

[NARRATOR]: That reputation system does not exist yet.

[VISUAL]: A-roll or full-screen text card: "That reputation system does not exist yet." Keep it plain and unambiguous.

[NARRATOR]: By default, the official desktop app keeps prompt and response plaintext in memory and writes only redacted metadata to its logs.

[VISUAL]: Screen recording of the desktop app settings or docs showing logging behavior where available, plus a simple label: "Plaintext in memory by default, redacted metadata in logs".

[NARRATOR]: Compute nodes and relays can both be self-hosted, so the strongest privacy story is running hardware you control.

[VISUAL]: Show self-hosted relay and compute-node documentation or repository interfaces, then A-roll for the privacy caveat.

[NARRATOR]: Third is danielsmith.io. It deploys as a static site, but that static site packs quite a punch.

[VISUAL]: Screen recording loading danielsmith.io, with a brief deployment artifact or static-site build output before the site appears.

[NARRATOR]: Three.js renders a decorated, lived-in house with two floors and a backyard.

[VISUAL]: Capture the Three.js house, moving camera through both floors and the backyard. Use real site footage only.

[NARRATOR]: You guide an avatar between points of interest representing my projects, experience, and personality.

[VISUAL]: Screen recording of avatar movement between project points of interest, experience markers, and personality details.

[NARRATOR]: The immersive experience includes a built-in tutorial.

[VISUAL]: Screen recording of the tutorial prompts and a short interaction completing one instruction.

[NARRATOR]: A dedicated text version serves visitors who prefer a conventional page or use screen readers.

[VISUAL]: Separately show the text version, keyboard navigation, conventional links, and accessible page structure. Avoid implying a screen reader if not recorded, but label "screen-reader friendly text version" if accurate.

[NARRATOR]: It gives hiring managers and recruiters a memorable first impression while whimsically capturing my interests in graphics programming and game development.

[VISUAL]: A-roll with the site open beside Daniel, then quick cuts between graphics programming details and game-like interactions.

[NARRATOR]: Together, these projects form a feedback loop.

[VISUAL]: Editor-made ecosystem diagram connecting Sugarkube, DSPACE, token.place, and danielsmith.io.

[NARRATOR]: DSPACE uses token.place for its built-in LLM chat NPC, dChat.

[VISUAL]: Screen recording of DSPACE dChat, the NPC selector, and the visible "Powered by token.place" integration where practical.

[NARRATOR]: Sugarkube hosts the relay and deploys all three projects through one staged release workflow.

[VISUAL]: Diagram arrow from Sugarkube to token.place relay and deployment arrows to DSPACE, token.place, and danielsmith.io. Overlay a staging-to-production release path.

[NARRATOR]: danielsmith.io acts as the front door.

[VISUAL]: Diagram highlights danielsmith.io as the entry point, then screen recording of navigating from the portfolio to project links.

[NARRATOR]: Each application exposes another weakness in the shared infrastructure, and every fix makes them easier to ship.

[VISUAL]: Animate the feedback loop: application need, infrastructure issue, Sugarkube improvement, easier deployment. Keep it simple and editor-made.

> 5:55–10:05: Electricity measurement and the efficiency-versus-agency tension

[NARRATOR]: My nine Raspberry Pi 5s each have 8 gigabytes of RAM, but only six are active, and even those are probably overkill for my traffic.

[VISUAL]: Rack overlay showing all nine Pi slots, with six active nodes bright and three inactive nodes dimmed. Add on-screen text: "9 × Pi 5, 8 GB RAM each | 6 active today".

[NARRATOR]: I was lucky enough to buy everything before the current Rampocalypse was in full swing.

[VISUAL]: A-roll for the joke, with a quick cut to receipt folders or BOM rows with all sensitive information redacted.

[NARRATOR]: For a fair comparison, I disconnected the three unused Pis and measured the PoE+ switch, along with any external cooling used during normal operation, through a `<power meter model>`.

[VISUAL]: Real footage of the three unused Pis being disconnected, then the PoE+ switch and continuously running desk fan plugged inside the measurement boundary. Show a labeled boundary overlay: "Included: active rack, PoE+ switch, desk fan / external cooling".

[NARRATOR]: Over `<measurement duration>` during `<representative conditions or workload>`, the setup averaged `<average watts>` watts, peaked at `<peak watts>` watts, and consumed `<measured kilowatt-hours>` kilowatt-hours.

[VISUAL]: Capture the power meter display or logging interface at representative moments, plus rack footage at idle and during workload. Add measured-value placeholders as on-screen text until final numbers are supplied.

[NARRATOR]: Across an average 730-hour month, that becomes `<monthly kilowatt-hours>` kilowatt-hours.

[VISUAL]: Simple calculation card: `<average watts>` × 730 hours = `<monthly kilowatt-hours>` kWh.

[NARRATOR]: At my marginal electricity rate of `<electricity rate>` per kilowatt-hour, it costs `<monthly electricity cost>` per month, or `<annual electricity cost>` per year.

[VISUAL]: Continue calculation card with electricity rate, monthly cost, and annual cost placeholders.

[NARRATOR]: That includes the switch, PoE losses, and cooling used during the test.

[VISUAL]: Measurement boundary diagram highlights switch, PoE losses, onboard fans, and the continuously running desk fan inside the included area.

[NARRATOR]: It excludes my shared router and modem, along with token.place compute nodes outside the rack.

[VISUAL]: Same boundary diagram grays out router, modem, and off-rack token.place compute nodes under "excluded".

[NARRATOR]: A separate GPU-enabled computer needs its own measurement.

[VISUAL]: A-roll for the caveat, or a simple excluded-device card labeled "GPU compute node: measure separately".

[NARRATOR]: For the cloud comparison, I modeled self-managed three-node staging and production clusters in one availability zone in AWS’s Oregon region.

[VISUAL]: Screen recording of the AWS calculator or a clean editor-made architecture diagram showing two self-managed three-node k3s clusters in one Oregon availability zone.

[NARRATOR]: The single availability zone mirrors the rack’s single-site failure domain.

[VISUAL]: Diagram places the home rack as one site beside one AWS availability zone. Label both "single-site failure domain".

[NARRATOR]: The model uses six on-demand Linux `c7g.xlarge` instances.

[VISUAL]: AWS calculator or architecture diagram highlights six `c7g.xlarge` instances.

[NARRATOR]: Their four Arm vCPUs and 8 GiB of memory roughly match each Pi’s resource shape, although the AWS instances are substantially faster.

[VISUAL]: Comparison table: "Pi 5 node: 8 GB RAM" beside "c7g.xlarge: 4 Arm vCPU, 8 GiB RAM, substantially faster".

[NARRATOR]: Each instance gets a 256 GiB gp3 volume and a public IPv4 address.

[VISUAL]: Add six 256 GiB gp3 volumes and six public IPv4 addresses to the AWS diagram.

[NARRATOR]: I kept k3s and Cloudflare Tunnel, excluding EKS, a managed load balancer, a NAT gateway, RDS, and managed observability.

[VISUAL]: Concise on-screen exclusions list: "Excluded: EKS, managed load balancer, NAT gateway, RDS, managed observability".

[NARRATOR]: Using AWS’s public rates from July 22, 2026, compute costs $635.10 per month, storage costs $122.88, and IPv4 addresses cost $21.90.

[VISUAL]: Readable cost table or animated stack labeled "Pricing snapshot: July 22, 2026" with rows for compute, storage, and IPv4.

[NARRATOR]: The fixed total is $779.88 per month, or $9,358.56 per year, before taxes, data transfer, snapshots, expanded monitoring, backups, or support.

[VISUAL]: Cost table totals to "$779.88/month" and "$9,358.56/year". Add small exclusions text: "Before taxes, data transfer, snapshots, expanded monitoring, backups, support".

[NARRATOR]: Discounts, smaller instances, or shutting staging down could lower that bill substantially, but would change this always-on, shape-matched comparison.

[VISUAL]: A-roll for the nuance, with on-screen text: "Discounts and smaller shapes change the comparison".

[NARRATOR]: AWS does not publish the direct power consumption of an individual instance, so this compares cost rather than watts.

[VISUAL]: A-roll for the distinction. Add on-screen text: "Financial comparison, not watt-for-watt energy comparison".

[NARRATOR]: Its newer hardware and data-center economies may win on performance per watt, but this experiment did not prove that.

[VISUAL]: Licensed stock data-center footage marked "illustrative" beside rack footage, with a neutral scale graphic labeled "not measured here".

[NARRATOR]: The full nine-node build cost me `<full nine-node BOM total>`.

[VISUAL]: Real hardware beauty shots, printed parts, cabling, and repository BOM. Show receipts only with names, addresses, order numbers, and payment details redacted.

[NARRATOR]: Excluding the three unused Pi node kits while retaining required shared equipment brought the comparable six-node cost to `<comparable six-node BOM total>`.

[VISUAL]: Simple comparison table: "Full nine-node total" versus "Comparable six-node total" with the three unused node kits visibly removed while shared equipment remains.

[NARRATOR]: The repository supplied the quantities; my receipts supplied the prices.

[VISUAL]: Split screen of repository BOM quantities and redacted receipt price lines.

[NARRATOR]: If local electricity costs less than $779.88 per month, simple cash break-even occurs after `<break-even months>` months.

[VISUAL]: Break-even card with the condition highlighted: "Local monthly electricity cost < $779.88" and placeholder result.

[NARRATOR]: That is the comparable six-node cost divided by the monthly savings over AWS, rounded up.

[VISUAL]: Show formula exactly: `comparable six-node cost / (AWS monthly cost - local monthly electricity cost)`. Optionally add a cumulative-cost line chart crossing at the break-even month.

[NARRATOR]: If local operating costs equal or exceed AWS, there is no positive break-even under these assumptions.

[VISUAL]: Same chart shows a no-crossing case labeled "No positive break-even if local operating cost ≥ AWS".

[NARRATOR]: This calculation also ignores my labor, failures, replacement parts, internet service, AWS discounts, and the value of managed infrastructure.

[VISUAL]: A-roll for the caveat with a concise exclusions checklist beside Daniel.

[NARRATOR]: A real lifecycle comparison would need to include manufacturing, shipping, embodied energy, and indirect water use on both sides.

[VISUAL]: A-roll continues, then cut to illustrative licensed footage of electronics manufacturing, shipping, grid infrastructure, and cooling water with labels making clear both local hardware and cloud infrastructure have indirect impacts.

[NARRATOR]: The rack itself uses no cooling water, unless you count what I drank while assembling it.

[VISUAL]: Real shot of Daniel taking a drink of water next to the rack, timed to the joke.

[NARRATOR]: There is no dedicated air conditioning, humidity control, or liquid cooling; just onboard fans and a desk fan.

[VISUAL]: Close-ups of onboard Pi fans and the continuously running desk fan. Do not imply there is no indirect water use from electricity or manufacturing.

[NARRATOR]: Running locally gives me more agency over energy use.

[VISUAL]: A-roll with the power meter and rack controls visible.

[NARRATOR]: I can meter the rack, choose its electricity source, schedule work around solar generation, power down unused environments, and own the means of production for this tiny corner of the internet.

[VISUAL]: Montage of power meter readings, deployment scheduling, staging environment being powered down, and licensed or real solar, battery, and inverter footage labeled "future off-grid plan" where appropriate.

[NARRATOR]: That control matters to me, even though it does not automatically make the homelab greener.

[VISUAL]: A-roll for the balanced conclusion, with on-screen text: "Agency ≠ automatic environmental win".

> 10:05–11:15: Participation and concluding vision

[NARRATOR]: All four projects are open source.

[VISUAL]: Screen recording of the four public repositories or project pages in a clean grid: Sugarkube, DSPACE, token.place, and danielsmith.io.

[NARRATOR]: You can play DSPACE and suggest quests, explore danielsmith.io, run a token.place compute node or relay, or try Sugarkube on your own Raspberry Pis.

[VISUAL]: Four quick practical demos: DSPACE gameplay and quest feedback path, danielsmith.io exploration, token.place desktop compute node or relay docs, and Sugarkube documentation for Raspberry Pi setup.

[NARRATOR]: Even testing the documentation and telling me where it breaks would help.

[VISUAL]: A-roll with a restrained on-screen callout: "Docs testers welcome".

[NARRATOR]: Very few people need a micro data center at home.

[VISUAL]: A-roll for the caveat, with the rack in frame but not glamorized as necessary gear.

[NARRATOR]: You can start with one Pi or an old computer.

[VISUAL]: Real shot of a single Raspberry Pi and an old computer on a desk, labeled "Start small".

[NARRATOR]: This yellow rack isn’t going to defeat AWS in single combat.

[VISUAL]: A-roll joke delivery. Optional simple on-screen text: "Not an AWS boss fight".

[NARRATOR]: I want Sugarkube to provide another option where people can own more of the stack, learn Kubernetes by running something real, and decide how their hardware and energy are used.

[VISUAL]: Montage of hands working on the rack, terminal deployment, Kubernetes dashboard or safe `kubectl` output, and power controls.

[NARRATOR]: Long term, I plan to run Sugarkube from a dedicated off-grid solar, battery, and inverter system.

[VISUAL]: Real or licensed stock solar panels, batteries, inverter, and charge controller footage. Clearly label: "Future plan: dedicated off-grid solar, battery, and inverter".

[NARRATOR]: Subscribe if you want to see that process!

[VISUAL]: A-roll with restrained on-screen text: "Subscribe for the off-grid build".

[NARRATOR]: I started Sugarkube because deploying my projects kept getting in the way of building them.

[VISUAL]: Screen recording of deployment workflow transitioning into feature work across the projects.

[NARRATOR]: Now they form one connected ecosystem, and the infrastructure is helping me move faster.

[VISUAL]: Return to the four-project ecosystem diagram, animating deployment and feedback-loop arrows one last time.

[NARRATOR]: It’s visible, measurable, modifiable, and mine.

[VISUAL]: Final sequence: Daniel on A-roll, quick cuts of repository pages and live application screens, then a final bright-yellow rack hero shot with LEDs and fans running.
