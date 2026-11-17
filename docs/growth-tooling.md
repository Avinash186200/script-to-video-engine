# Growth tooling

The engines turn scripts into videos. These tools handle what comes after: testing thumbnails and titles, writing
pinned comments, preparing Shorts for upload, and publishing lesson pages. Every tool reads a data file and writes
files. None of them calls the YouTube API or uploads anything; publishing stays a human step.

## The channel config

Everything specific to one channel lives in a JSON file, never in code:

```bash
cp channel.example.json channel.json     # git-ignored
```

The tools look for `--config`, then `VE_CONFIG`, then `./channel.json`. `VE_SERIES`, `VE_REPO_URL`,
`VE_MAIN_PLAYLIST_URL` and `VE_SHORTS_PLAYLIST_URL` override the file.

| Key | Meaning |
|---|---|
| `series`, `repo_url` | Shown in metadata and lesson pages |
| `main_playlist_url`, `shorts_playlist_url` | Playlist links added to descriptions and the lesson index |
| `episodes` | Episode id -> `video_id`, `label`, `code` folder, optional quick-check `question` |
| `shorts` | Short id -> `{"episode": "<episode id>"}` or `{"video_id", "label"}`; add `title` + `short_id` to list it in the lesson index |
| `default_related` | The video a Short links to when nothing else matches |
| `pinned_comment.template` | Template with `{question}`, `{code_url}`, `{notes_url}`, `{next_url}` |

## Thumbnails: batch, then A/B

`videoengine.hooks` renders one thumbnail per row of a CSV (`id,hook,highlight,visual,tag`) and contact sheets of
twelve, so a whole series can be reviewed at a glance. Each hook is checked first: the highlight word must be in
the hook, at most three lines, at most six words, and a known visual.

`videoengine.ab_thumbs` renders challenger variants for selected videos and puts them on one sheet, next to the
live thumbnail when you give its path. Run the test (YouTube's built-in thumbnail test, or a manual swap for a fixed
window), then score it:

```bash
python -m videoengine.growth ab --a 4000 120 --b 4100 165
# CTR A 3.00%  B 4.02%  lift +34.1%  z 2.50  p 0.0124  -> B
```

The verdict is `not enough data` below 1,000 impressions per arm (change it with `--min-impressions`), and
`no difference` when p is 0.05 or more. A two-proportion z-test assumes the two arms saw similar traffic; a
manual swap over two different weeks does not guarantee that, so treat a borderline result as a tie.

## Title experiments

`growth titles` reads a CSV of `video_id,old_title,new_title,keyword,start_date` and:

- checks each new title: not empty, at most 100 characters, no `<` or `>`, not all caps, no banned word
  (from `banned_words.txt`);
- reports whether the keyword sits in the first ~60 characters, the part a phone shows;
- writes `title_changes.md` with the old title kept for rollback and a review date 14 days after the start.

Change one thing at a time. If you change a title and a thumbnail on the same day, the CTR change cannot be
attributed to either.

## Pinned comments

`growth pinned` writes one comment per episode, in config order: the quick-check question, the code folder, the
lesson notes page and the next episode (the playlist for the last one). A line whose fields are missing is dropped,
so an episode without a question gets no empty "Quick check" line. Output: `pinned_comments.json` and
`pinned_comments_paste.txt` for copy-paste.

## Shorts in batches

`videoengine.batch_shorts` writes many Short scripts from one JSON spec (see
`examples/shorts_batch.example.json`). Shared fields go in `defaults`. The spec is validated before anything is
written: unique ids, titles of 100 characters or less, every beat as `[headline, say, visual]`, and the cover
highlight inside the hook. Existing scripts are not overwritten without `--force`, so hand edits are safe.
`--covers DIR` also renders a vertical cover per Short.

## Upload prep

`videoengine.upload_prep` copies each rendered Short (`video.mp4`, `captions.srt`) to `upload/shorts/` and writes a
`.txt` with the title, the description (body, full-episode link, playlist link, hashtags plus `#Shorts`), tags and
a `RELATED_VIDEO` line.

Which long video a Short links to is looked up, in order:

1. `META["related_video"]` in the Short script;
2. the config `shorts` map by exact id, then by number prefix (`s07` matches `s07_mcp`, so renaming a Short does
   not break the link);
3. `META["source_episode"]` when it is an episode id in the config;
4. `default_related`;
5. nothing: the Short is still prepared, without an episode link, and the run says so.

A Short whose title is over 100 characters or whose description contains `<` or `>` is skipped and the command
exits non-zero.

## Lesson pages

`videoengine.lessons` turns lesson scripts into one Markdown page each, plus an index: video link, clickable
chapters (from `output/<id>/youtube.txt` when the lesson has been built), the slide content and the full narration,
and previous/next links. A lesson with no `video_id` in the config gets a page without the watch link. Every page is
checked against `banned_words.txt` before it is written.

## Sample inputs

- `examples/lessons/arch_evolution.py`: a full ten-minute lesson on how AI assistant architecture evolves.
- `examples/shorts/s48`-`s52`: five Shorts cut from that lesson.
- `examples/*.example.csv` / `*.example.json`: one input file for each tool above.

## Tests

`tests/test_growth_tools.py` covers the pure functions: config precedence, every step of the Short-to-episode
lookup, description building and checks, spec validation and generated script source, hook checks, title checks,
the CTR test verdicts, pinned-comment templating and lesson page building. No rendering, no network.
