# Tribe v2 and Video Virality

This workspace now includes a compact README for the Tribe v2 experiment and the report-first workflow behind it.

The source material I reviewed is split between the pipeline docs and the generated report set under `report/run_20260412-132433/`. The report is the main article: it shows how TRIBE v2 was used to score videos, identify peaks and dead zones, and turn those scores into editing guidance for virality-focused content.

## What Tribe v2 Is Doing

TRIBE v2 is the neural scoring layer in this repo. In this project it is used to:

- predict per-second engagement from video, audio, and text inputs
- label timeline segments as `peak`, `good`, `weak`, or `dead`
- surface hook strength with a hook ratio and first-5-second mean
- support a report that explains why a video performs well or poorly

This repo does not treat TRIBE v2 as a magic virality oracle. The useful part is the combination of:

- the raw timeline scores
- the merged segment labels
- the retrieval-style video analysis
- the final written synthesis

## Repo Layout

- `viral-detector-post.md` is the main article-style writeup
- `README.md` in the source repo explains the local pipeline and output layout
- `report/run_<timestamp>/` contains full experiment runs
- `report/run_<timestamp>/videos/<niche>/report.md` is the most useful output for reading the analysis
- `scripts/generate_report.py` assembles the markdown report and chart for one video folder
- `scripts/tiktok_tribev2_pipeline.py` runs the scrape, download, TRIBE inference, and artifact generation pipeline

## What The Report Shows

Across the generated niche reports, the same patterns repeat:

- strong openings matter, but a strong hook alone is not enough
- visual novelty and fast payoff beat static or repetitive sections
- dead zones appear when the content becomes predictable, textual, or purely transitional
- long-form videos can have excellent hook ratios and still underperform on reach
- follower count helps, but format and structure often matter more

### Concrete examples from the report

- In the skincare report, the most viral content is driven by a visceral extraction moment, not the clean result.
- In the looksmaxxing report, a long persuasive essay has the strongest hook ratio in the set, but it still gets far fewer plays than short-form spectacle.
- In the dailylike report, direct eye contact and a clear, simple premise outperform a softer, static presentation.

## How To Read The Output

The report format is designed to answer four questions:

1. What is the video?
2. Where does engagement spike or collapse?
3. Which segments are peaks, good, weak, or dead?
4. What should be changed in a re-edit?

The most useful sections are:

- `TRIBE Summary` for overall score and hook ratio
- `Merged Segments` for the actual edit boundaries
- `TRIBE Timeline` for the second-by-second score curve
- `Final Report` for the plain-English recommendation layer

## Practical Takeaway

If you are using Tribe v2 as a video virality metric, the main value is editorial:

- move the highest-engagement moment earlier
- cut dead zones aggressively
- vary the visual pattern before repetition sets in
- keep the opening legible in the first few seconds
- use the report to explain *why* one version outperforms another

## Reproducing The Workflow

Typical workflow:

1. Run the niche scrape/download pipeline.
2. Run TRIBE inference on the selected videos.
3. Generate per-video and per-niche markdown reports.
4. Read the report first, then edit the video based on the timeline.

The report is the product. TRIBE v2 is the scoring system underneath it.
