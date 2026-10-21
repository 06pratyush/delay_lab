# Contributing to Delay Lab

Thanks for helping! Delay Lab is a small teaching and experiment tool. It shows why AR suffers
from headset delay more than VR, using a laptop webcam. Contributions of every size are welcome.

By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
**Found a security problem?** Don't open an issue. See [SECURITY.md](SECURITY.md).

## Ways to help

| You want to… | Start here |
|---|---|
| Report a bug | [Open a bug report](https://github.com/06pratyush/delay_lab/issues/new?template=bug_report.yml). Include the self-test output (see below). |
| Suggest a feature | [Open a feature request](https://github.com/06pratyush/delay_lab/issues/new?template=feature_request.yml) *before* writing code. |
| Fix something small | Typos, docs and clear one-line bugs can go straight to a pull request. |
| Pick up a task | Look for issues labelled [`good first issue`](https://github.com/06pratyush/delay_lab/labels/good%20first%20issue). |
| Share a measurement | Open an issue with your `results/sweep.csv`, your webcam model and how you recorded it. Real results from other webcams are very welcome. |

Ideas already on the wish list:
- **Timewarp:** last-moment correction as a fourth mode.
- **ArUco markers:** track a printed marker instead of the nose.
- **Linux and macOS:** test and document support.
- **WebXR:** a real headset version.

## Set up a development environment

Delay Lab targets **Windows 10/11 with Python 3.11**. MediaPipe can lag behind newer Python releases.
macOS and Linux should work from source but are not tested yet. Reports are welcome.

```bash
git clone https://github.com/<you>/delay_lab.git    # your fork
cd delay_lab
py -3.11 -m venv .venv
.venv\Scripts\activate                               # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python download_model.py                             # one-time, ~4 MB face model (not committed)
python app.py --selftest 8                           # needs a webcam; checks everything end to end
```

Only for building the exe: `pip install -r requirements-build.txt`, then run `python build_exe.py`.

## Run the tests

```bash
python -m pytest                 # fast, no webcam or model needed
```

- CI runs the same command on **Windows with Python 3.11** for every push and pull request. It must be green before merging.
- **Keep tests webcam-free.** Test logic with synthetic data, like the sine-wave head tracks in `tests/test_sweep.py`, not with real recordings.
- If you change anything the camera touches (`app.py`, `tracker.py`, `render.py`), also run `python app.py --selftest 8` and paste its summary into your pull request.
- If you change a chart or figure, run `python docs/make_figures.py` and check the images in `docs/img/`.

## Code style

Match the code around you:

- Python 3.11, type hints, and `from __future__ import annotations` in modules that use them.
- Small, single-purpose modules. The data flow is `tracker` → `delay` → `render` / `sweep`, with `app` wiring them together.
- Comments explain *why*, not *what*. Keep docstrings short.
- New dependencies need a reason. Raise them in an issue first: the exe already bundles about 130 MB.
- Charts use the shared colours and style in `chart_style.py`.
- Files are UTF-8 with LF line endings.

## Be honest about results

This project measures things, so every number and chart must say what it is:

- **Measured:** a real recording. Say how long it was, which webcam, and how you moved.
- **Calculated:** from a formula, such as *slip = speed × delay*.
- **Synthetic / predicted:** generated data run through the real code.
- **Illustration:** example numbers in a drawing.

Never present a synthetic chart or a short test clip as a result. If a measurement contradicts the
expected result, that's worth reporting too.

## Privacy

`recordings/`, `logs/` and `results/` are git-ignored because they can contain people's faces.
**Don't commit recordings or GIFs of anyone who hasn't agreed to it.** That includes screenshots
in issues and pull requests.

## Branches and commits

**Branch** from `main` in your fork, and name the branch after the change:

| Prefix | For |
|---|---|
| `feat/…` | new features (`feat/timewarp-mode`) |
| `fix/…` | bug fixes (`fix/sweep-empty-video`) |
| `docs/…` | documentation only |
| `test/…`, `refactor/…`, `ci/…`, `build/…` | everything else |

**Commit messages** follow [Conventional Commits](https://www.conventionalcommits.org/), like the existing history:

```text
<type>(<optional scope>): <what changed, imperative, under ~72 characters>

<optional body: why the change was needed and anything surprising>
```

- **Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `ci`, `build`, `chore`.
- **Common scopes:** `app`, `tracker`, `delay`, `render`, `sweep`, `charts`.
- **Examples from this repo:**
  - `feat(delay): guess-ahead prediction and AR + fix mode`
  - `feat(sweep): tracker-jitter noise floor on the chart and CSV`
- **Keep commits small:** one logical change per commit is easier to review than one big commit.

## Pull request process

1. **Open or find an issue first** for anything bigger than a small fix, so we can agree on the approach before you spend time on it.
2. **Keep the pull request focused** on one change. Rebase on the latest `main` if it has moved.
3. **Fill in the pull request template:**
   - what changed and why;
   - the linked issue (`Closes #123`);
   - how you tested it (pytest, plus self-test output when camera code changed);
   - screenshots for visual changes.
4. **Update the docs** (README, docs/) when you change behaviour, keys or output files.
5. **Make sure CI is green.** A pull request with failing tests can't be merged.
6. **Review:** the maintainer aims to reply within about a week. Please answer review comments with new commits rather than force-pushing, so the conversation stays readable.
7. **Merge:** pull requests are squash-merged, so the pull request title becomes the commit message. Write the title as a Conventional Commit too.

## License

By contributing, you agree that your contributions are licensed under the project's
[MIT License](LICENSE).
