# Security policy

Delay Lab is a local desktop app: it reads your webcam, runs face tracking on your own
computer and writes files next to itself. It has no accounts, no server and no telemetry.
Its only network access is the one-time model download in `download_model.py`. Security
problems are still possible, and we'd like to hear about them privately first.

## Please don't open a public issue

A public issue shows everyone how to exploit the problem before there is a fix.
Report it privately instead, in one of these ways:

1. **Preferred: GitHub private reporting.** Go to the repository's
   [**Security** tab → **Report a vulnerability**](https://github.com/06pratyush/delay_lab/security/advisories/new).
   Only the maintainer can see the report, and we can discuss and fix it together there.
2. **Fallback: email** the maintainer at **vnpratyush2006@gmail.com**, with
   `[delay_lab security]` in the subject line.

## What to include

- What the problem is, and what an attacker could do with it.
- Steps to reproduce: a minimal file, command or video, if one is needed.
- Which version you tested: a commit hash or release tag, and whether you ran it from source or `DelayLab.exe`.
- Your Windows and Python versions.
- Any fix you would suggest (optional).

Please don't include recordings of other people's faces.

## What happens next

Delay Lab is maintained by one person in their spare time, so these are best-effort targets, not guarantees:

| Step | Target |
|---|---|
| Acknowledge your report | within 7 days |
| Confirm the problem, or explain why it's not one | within 14 days |
| Release a fix, or agree a timeline with you | as soon as practical, depending on severity |

You'll be credited in the advisory and release notes, unless you'd rather stay anonymous.
Please give us a reasonable chance to fix the problem before you disclose it publicly.

## Supported versions

| Version | Supported |
|---|---|
| `main` (latest) | ✅ |
| Latest `v1.x` tag | ✅ |
| Older tags | ❌ (please update first) |

## In scope

- Code execution or file writes outside Delay Lab's own folders, triggered by a crafted video, CSV or model file.
- Problems in how `download_model.py` fetches and stores the model.
- Problems in how `build_exe.py` packages `DelayLab.exe`.
- Recordings, logs or results ending up somewhere other than the `recordings/`, `logs/` and `results/` folders.
- A known vulnerability in a pinned dependency that actually affects Delay Lab.

## Out of scope

- Someone with full access to your computer reading files you recorded. That's how local files work.
- Vulnerabilities in MediaPipe, OpenCV, NumPy, pandas, matplotlib or PyInstaller themselves.
  Report those upstream. Do tell us if Delay Lab needs to update a dependency.
- The webcam light turning on while the app is running. It's meant to.
