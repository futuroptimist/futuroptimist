# Sugarkube (working title) (2026-09-01)

> Draft script for video `<youtube_id>`

> Draft outline

> 0:00–0:40 — physical hook, environmental concern, and honest thesis
> 0:40–1:20 — deployment tax and SRE motivation
> 1:20–2:40 — Sugarkube hardware, k3s platform, and command layer
> 2:40–3:45 — DSPACE, token.place, and danielsmith.io as ecosystem proof
> 3:45–5:45 — measured electricity and the efficiency-versus-agency tension
> 5:45–6:30 — participation and concluding vision

## Script

> 0:00–0:40 — Physical hook, environmental concern, and honest thesis

AI feels like it lives in the cloud, but the cloud is physical. Data centers place concentrated demands on electrical grids; many use water for cooling, and nearby communities can feel those impacts. So I built this: Sugarkube, a bright-yellow rack of nine Raspberry Pis hosting my open-source projects. It won’t replace the cloud, and it may not beat it on raw efficiency. But it lets me see, measure, and control more of the infrastructure behind my software. I want to find out how much that local control matters.

> 0:40–1:20 — The deployment tax and my SRE motivation

I’ve spent more than a decade building production software, including nearly seven years as a site reliability engineer at YouTube. I’ve been on-call for large-scale, globally distributed systems, so I know how much work reliable services require. With my own projects, though, the bottleneck usually isn’t writing code. It’s packaging, deploying, verifying, updating, and recovering from failures. I have way too many passion projects—as you can see on my GitHub—so every one-off deployment path takes time away from improving them. Sugarkube is my attempt to make that work repeatable.

> 1:20–2:40 — What Sugarkube actually is

Cloud services from AWS, Google Cloud, DigitalOcean, Netlify, and Vercel already offer relatively easy ways to deploy small apps—especially with a trusty LLM whispering in your ear. I wanted a homegrown path that kept a common infrastructure layer visible: Kubernetes.

Sugarkube runs k3s, a lightweight Kubernetes distribution suited to edge devices, homelabs, and single-board computers. My rack is three bright-yellow PLA tiers, each holding three Raspberry Pi 5s powered and networked through one unmanaged PoE+ switch. The repository includes the printable designs, tooling to build a Raspberry Pi OS image with k3s preinstalled, and a command layer built around the open-source runner `just`.

A `justfile` stores project-specific commands as recipes. Sugarkube uses them for high-level workflows like bootstrapping a cluster, onboarding an application, deploying and verifying it, promoting it to production, and rolling it back. The goal isn’t to hide Kubernetes. It’s to make common workflows approachable while keeping the underlying manifests, Helm charts, and infrastructure visible.

> 2:40–3:45 — The ecosystem running through it



> 3:45–5:45 — Electricity measurement and the efficiency-versus-agency tension

My nine Raspberry Pi 5s, each with 8 gigabytes of RAM, are probably way overkill for my current traffic; several lightweight services could run on much smaller hardware. I was lucky enough to get all of my hardware before the current Rampocalypse was in full swing.



> 5:45–6:30 — Participation and concluding vision

