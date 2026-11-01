# TECH-G blog: Hugo migration and redesign

Status: draft for approval
Date: 2026-11-02
Owner: Jihyeon Gim (potatogim)
Site: https://tech.gluesys.com (repository `gluesys/tech-blog`)

## 1. Intent

TECH-G is Gluesys' developer blog. It started as the "AnyStor-E TECH" product
blog and was rebranded to TECH-G in December 2019. It still runs on a 2015-era
Jekyll theme (Bourbon/Neat, jQuery 1.11, FlexSlider, Disqus) built by the
GitHub Pages legacy builder. Several features silently do not work there
(for example `jekyll-archives` tag pages return 404), the layout has fixed
240px + 960px widths that break on phones, the fonts have no Korean glyphs,
and there is no search.

This project replaces the whole stack and the visual design in one move,
without losing anything that is already published.

Why these choices:

- **Hugo** instead of a JavaScript framework: a single pinned binary, no
  `node_modules`, no npm supply chain. The owner explicitly rejected both npm
  tooling and the npm ecosystem's supply-chain risk, and rejected React and
  Svelte.
- **Tags are the primary navigation axis.** The original authors intended
  posts to belong to several topics at once, which is why the three planned
  categories (knowledge sharing / issue cases / test data) were abandoned.
  Series exist but are a secondary aid, never the main structure.
- **The visual design follows the company CI** (https://gluesys.com/company/overview/)
  and keeps the intent of the old design: an isometric storage illustration
  in the hero, white content on a calm background, and the TECH-G name.

## 2. Goals, non-goals, anti-goals

Goals

1. Lossless migration of all 51 posts on `origin/master`: same URLs, same
   heading anchors, same images, same footnotes, same feed URL.
2. Korean-friendly reading experience on desktop and phone.
3. Site search that works acceptably for Korean queries.
4. Tag-based browsing with cleaned-up tags (bilingual duplicates merged).
5. A CI-aligned visual identity (section 8), with light and dark themes.
6. Build and deploy by GitHub Actions to GitHub Pages, with migration
   verification checks that fail the build.

Non-goals (this project)

- Rewriting or editing post content, covers, or thumbnails.
- Deleting unreferenced assets (114 files, 3.8 MB). They are kept; cleanup is
  a later, separate decision.
- Automatic per-post OG image generation.
- Migrating Disqus comment history into giscus (see section 13).
- Multi-language (English) site.

Anti-goals (would make this a failure even if it builds)

- Any published URL, heading anchor, or image that worked before now 404s or
  points somewhere else.
- Any npm, `package.json`, or `node_modules` anywhere in the repository or the
  CI pipeline.
- A templated "AI-generated" look: one phrase in the headline colored
  differently, all-caps eyebrow labels, `A - B - C` meta strings, identical
  rounded cards with soft shadows, gradient washes as decoration.
- Modifying the company CI symbol (shape or colors).
- Generated images that look like factual material (product screens,
  hardware photos, benchmark charts).

## 3. Constraints

- **Tooling:** Hugo (extended edition, pinned version) and the Pagefind
  standalone binary (pinned version). Both are downloaded in CI from their
  GitHub releases and verified with SHA-256 checksums committed to the
  repository. All third-party GitHub Actions are pinned by commit SHA.
- **Front-end code:** plain CSS and TypeScript. TypeScript is bundled with
  Hugo's built-in `js.Build` (esbuild). No runtime libraries. Type checking,
  if wanted, may use `deno check` (single binary); it is optional.
- **Helper scripts** (conversion and verification) are Python 3 using only
  the standard library.
- **Approvals:** local commits on the migration branch are free (small,
  task-sized commits are expected). Pushes, PRs, and any GitHub setting
  change (enabling Discussions, switching the Pages build source) happen only
  with the owner's explicit approval.
- **Base branch:** work from `origin/master` (the local `master` checkout is
  5 commits behind; the newest 4 posts and a footnote fix exist only on
  `origin/master`).
- **Fonts:** self-hosted, no font CDN at runtime. Licenses (SIL OFL) are
  committed next to the font files.
- Keep Google Analytics 4 with the existing ID `G-7Y6MG4Q2JR`.

## 4. Current state (facts the builder needs)

- 51 posts in `_posts/blog/`. Every post has the same front matter keys:
  `layout`, `title`, `date`, `author`, `categories` (always `blog`), `tags`,
  `cover`, `main`. No Liquid (`{{` or `{%`) appears in any post body.
- Post URL rule: `/blog/{front-matter date as YYYY/MM/DD}/{filename slug}.html`.
  The date comes from front matter, **not** the filename. Eight posts differ:

  | File | Published path date |
  |---|---|
  | storage_1_intro | 2019/12/02 |
  | after_infra_seminar | 2020/04/16 |
  | NVMe_1 | 2021/03/03 |
  | composableinfra | 2021/10/26 |
  | SPDK_1 | 2022/02/18 |
  | CSI | 2022/06/21 |
  | lustre_GPU_Direct_Storage | 2022/07/22 |
  | Lustre_FID_2 | 2025/09/01 |

  44 slugs contain capitals or underscores and must not be lowercased. Four
  posts have a time in `date`; the site has no timezone set, so dates are UTC.
- Pages returning 200 today: `/`, `/page2/` to `/page6/`, `/posts/`,
  `/tags/` (tag anchors as `/tags#<tag>`), `/blog/`, `/about/`, `/feed.xml`,
  `/sitemap.xml`, `/robots.txt`, `/googlea2b9a3ab05f01437.html` (Search
  Console verification, must stay byte-identical), `/assets/icons/favicon.ico`.
  `/category/blog/` and `/tag/<name>/` are 404 today and need nothing.
- `/feed.xml` is RSS 2.0 with the latest 10 posts and full content.
- Markdown features in use (kramdown):
  - `{: width="..."}` image attributes: 107 in 32 posts.
  - `{::nomarkdown}` blocks: 10 in 2 posts.
  - Footnotes: 106 definitions in 24 posts, one footnote reference inside a
    table.
  - Captions written as `<center>&#60; caption &#62;</center>`: 111 in 32 posts.
  - Raw HTML in 35 posts, one SlideShare `<iframe>`, `<br>` in 6 posts.
  - Hard line breaks by two trailing spaces: 610 places in 37 posts.
  - `&nbsp;` paragraphs used as vertical spacers.
  - Emoji shortcodes (jemoji): `:clap:`, `:wave:`, `:bulb:`.
  - Indented code blocks: 165 lines in 8 posts.
  - Fenced code languages: console, c, C, bash, perl, powershell, shell,
    yaml, text, sh, and 18 fences with no language.
  - `{:target="_blank"}` on 3 links.
  - 41 image paths containing spaces (all in the TrueNAS post).
- Heading IDs: 495 headings, 431 of them Korean, no duplicates. 48 in-page
  table-of-contents links depend on them.
- 33 absolute internal links between posts, some with text fragments
  (`#:~:text=`).
- Assets: 390 files, 108 MB under `/assets/`; zero missing references.
  `/assets/penpot/docker-compose.yaml` is a download link and must keep
  working. `/public/slide01.jpg` and `/public/slide02.jpg` are old hero images.
- Tags: 252 distinct, 183 used once, average 8 per post. Bilingual pairs
  (`Storage`/`스토리지`, `Backup`/`백업`, `NAS`/`네트워크 결합 스토리지`) and
  spelling or case variants (`재해 복구`/`재해복구`, `파일 시스템`/`파일시스템`,
  `File System`/`file system`/`Filesystem`, `Fibre Channel`/`Fibre channel`,
  `Software Defined`/`software defined`, `Software Defined Storage`/
  `software defined storage`). The MOP post has `tags: MOP` as a scalar, not
  a list.
- Series present in the content: 스토리지 기초 지식 (11), 스토리지 이중화 (2),
  소프트웨어 정의 스토리지 (2), NVMe (3), SPDK (2), NVMe 시대의 RAID (2),
  Lustre 분석 (2).
- A reference snapshot of the live site (51 post HTML pages, live URL list,
  live sitemap) was captured during design. The builder re-captures it at
  implementation time (section 11) instead of relying on the design-time copy.

## 5. Content migration

### 5.1 Conversion script

`tools/convert_posts.py` reads Jekyll posts from `_posts/blog/` and writes
Hugo content to `content/blog/`. It is **idempotent**: re-running it on a
newer `origin/master` regenerates the same output, so posts merged during the
migration window are picked up at cutover by running it again.

Per post it does the following, and nothing else:

1. **Front matter.** Keep `title`, `date`, `author`, `cover`, `main`. Write an
   explicit `url:` equal to the live path (section 4 rule). Write canonical
   `tags:` from the alias map (5.3) and keep the original value verbatim as
   `legacy_tags:`. Drop `layout` and `categories`. Add `series:` and
   `series_order:` for posts in the known series (5.4).
2. **Heading IDs.** Append an explicit Goldmark attribute `{#id}` to every
   heading, with the ID taken from the live snapshot of that post, matched by
   heading order and text. Fail if counts or texts do not match.
3. **Image widths.** `![alt](src){: width="N"}` becomes raw
   `<img src="src" alt="alt" width="N" loading="lazy">`.
4. **Paths with spaces.** Percent-encode spaces in Markdown link and image
   destinations.
5. **`{::nomarkdown}` / `{:/}`** wrappers are removed; their inner HTML stays.
6. **`{:target="_blank"}`** links become raw
   `<a href="..." target="_blank" rel="noopener">`.
7. Everything else stays byte-for-byte: `<center>` captions, `&nbsp;` spacers,
   trailing-space line breaks, raw HTML, footnotes, emoji shortcodes, indented
   code, fence languages.
8. The script fails loudly on any kramdown syntax it does not recognize, and
   prints a per-post summary of what it changed.

### 5.2 Hugo settings that the migration depends on

- `markup.goldmark.renderer.unsafe = true` (raw HTML).
- `markup.goldmark.parser.attribute.title = true` (heading IDs).
- `markup.goldmark.extensions.footnote = true`; footnote IDs must match the
  live `fn:N` / `fnref:N` form (verified in section 11).
- `enableEmoji = true`.
- `disablePathToLower = true`.
- `timeZone = "UTC"`.
- Code highlighting by Chroma at build time; highlight.js is removed.

### 5.3 Tag aliases

`data/tag_aliases.yaml` maps every raw tag to one canonical tag. Policy:

- One canonical tag per concept.
- Korean label where an established Korean term exists (`스토리지`, `백업`,
  `재해 복구`, `파일 시스템`); the product or standard name where that is what
  people search for (`ZFS`, `NVMe`, `Lustre`, `CXL`, `SPDK`, `LVM`).
- Case and spacing variants always merge.
- The builder drafts the full map; the owner reviews it once as a table
  (raw tag, canonical tag, post count) before conversion is final.

`tools/check_tags.py` runs in CI and warns when a new post uses a tag that is
not canonical.

### 5.4 Series

Optional front matter `series` (name) and `series_order` (number). A post in a
series shows a compact box listing the other parts. A `/series/` index page
lists all series. Series never appear in the main navigation.

### 5.5 Static files kept as-is

Under `static/`: `assets/` (all 390 files, unchanged paths), `public/`
(old hero images, in case external pages link to them), `CNAME`,
`googlea2b9a3ab05f01437.html`, `robots.txt` (updated sitemap URL only if it
changes, which it should not).

### 5.6 URL preservation map

| Old URL | New behavior |
|---|---|
| `/blog/YYYY/MM/DD/slug.html` (51) | Same URL, the post |
| `/` | New home |
| `/posts/` | Full archive (canonical) |
| `/blog/` | Redirect page to `/posts/` (Hugo alias) |
| `/page2/` to `/page6/` | Redirect pages to `/posts/` |
| `/tags/` | Tag index; a small script maps `/tags#<raw tag>` to `/tags/<canonical>/` |
| `/about/` | New about page (content from the owner) |
| `/feed.xml` | Same URL, RSS 2.0, latest 10, full content |
| `/sitemap.xml`, `/robots.txt` | Same URLs |
| `/googlea2b9a3ab05f01437.html`, `/assets/icons/favicon.ico` | Unchanged files |

New URLs: `/tags/<tag>/`, `/series/`, `/search/`.

## 6. Information architecture

Main navigation: 글 (`/posts/`), 태그 (`/tags/`), 소개 (`/about/`),
채용 (external careers page), search.

- **Home:** hero with headline and search box; recent posts list (8); side
  column with featured tags (`data/featured_tags.yaml`, with post counts) and
  the series list; link to the full archive.
- **Archive `/posts/`:** all posts, newest first, grouped by year.
- **Tag index `/tags/`:** tags used by two or more posts shown prominently with
  counts; single-use tags in a collapsed list.
- **Tag page `/tags/<tag>/`:** posts with that tag.
- **Post:** tags, title, author, date, reading time, body, sticky table of
  contents (desktop), series box if any, tags, previous and next post,
  related posts (Hugo `.Related` on tags), careers call-to-action, comments.
- **Search `/search/?q=`:** full results page; the header search opens an
  overlay with the same engine. `/` focuses search.

## 7. Features

Included:

- Korean typography (section 8), `word-break: keep-all`.
- Sticky table of contents with current-section highlight (desktop only).
- Code blocks: language label, copy button.
- Copy link and native share (`navigator.share`, falling back to copy).
- Reading time computed for Korean: characters / 500 per minute, rounded up.
- Author card from `data/authors.yaml` keyed by email (name, short bio,
  optional avatar). Emails are not displayed. *(Builder's call, see 12.)*
- RSS feed, sitemap, Open Graph and Twitter meta (post `cover` as image,
  site default otherwise).
- Light and dark themes: follows the OS by default, with a toggle that is
  remembered per browser.
- giscus comments (section 9.2), loaded lazily when the comment area is near
  the viewport.
- Careers call-to-action at the end of each post, linking to the company
  careers page.

Out of scope now: automatic OG images, newsletter, view counters, likes.

## 8. Visual design

### 8.1 Brand basis

From the Gluesys CI page: the symbol is a letter G inside a hexagon, in two
blues; the wordmark is a wide geometric sans in gray. The hexagon is the same
outline as an isometric cube seen head-on, which is also the shape language of
the old TECH-G illustration. The design builds on that link.

Header lockup: **original CI symbol + "TECH-G"**, with "글루시스 기술 블로그"
as a small second line. The symbol is never recolored or reshaped. The
company wordmark `GLUESYS` is not used in the header.

### 8.2 Color tokens

| Token | Light | Use |
|---|---|---|
| `--ci-deep` | `#163CCF` | Hero background, call-to-action background, avatar |
| `--ci-bright` | `#1775FD` | Links, buttons, current TOC item, hexagon markers |
| `--ci-gray` | `#6A6E7F` | Dates, reading time, secondary text |
| `--ci-navy` | `#274B6B` | Code block background |
| `--ci-cyan` | `#00C3D2` | Keyboard focus ring, code highlight accents only |
| `--ink` | `#1C2233` | Body text |
| `--line` | `#E3E6EE` | Dividers, borders |
| `--soft` | `#F4F6FB` | Tag chips, footer |

`#5BCF13` (CI green) is not used. Dark theme tokens are derived by the builder
from the same hues (navy-based background, `--ci-bright` lightened for link
contrast) and must meet WCAG AA contrast for body text and links. The CI
symbol in dark mode uses an official reversed or white version from the
design team (section 13); until then it sits on a small light tile.

### 8.3 Type

- **Pretendard** for all Korean and Latin text. Body 17px desktop / 16.5px
  phone, line height 1.75. Article body max width 720px.
- **Saira** (width 125, weight 700) only for the "TECH-G" name, echoing the
  wide CI wordmark. Subset to the glyphs needed.
- Code: system monospace stack.

### 8.4 The one bold element: hexagon geometry

Used only for: section heading markers, tag chips (long hexagon with 30°
ends), the current-item marker in the TOC, author avatars. Everything else is
quiet: no card shadows, no gradient decoration, left-aligned text, hairline
dividers between list items.

### 8.5 Layouts

The approved mockup is the final (v2) version, approved by the owner on
2026-11-02. Its files and screenshots are committed next to this document in
`docs/superpowers/specs/2026-11-02-blog-hugo-redesign/` (`home.html`,
`post.html`, `style.css`, `shot-home-desktop.png`, `shot-post-desktop.png`,
`shot-home-mobile.png`). They are the reference:

- Home desktop: white header; `--ci-deep` hero with headline, one sentence,
  search box on the left and the illustration on the right; two-column body
  (recent posts list with right-side thumbnail, side column with tags and
  series); light footer with the symbol and links.
- Post desktop: tags, title, byline; 720px body with a 240px sticky TOC on
  the right; after the body, tags, previous/next, careers call-to-action.
- Phone: menu button replaces navigation; hero text and search on top with the
  illustration below; post list with square thumbnails; no TOC sidebar.

The builder ports these into Hugo templates; they are a visual reference, not
production code. Earlier exploratory mockups under `.superpowers/` are
superseded and not a reference.

Copy used in the mockups:

- Headline: 소프트웨어로 스토리지를 만드는 개발자들의 기술 이야기
- Sub: 파일 시스템, NVMe, 고가용성까지 글루시스 개발자가 직접 겪고 정리한 내용을 공유합니다.
- Search placeholder: ZFS, Lustre, 스냅샷처럼 주제로 검색
- Careers: 글루시스는 파일 시스템과 스토리지 소프트웨어를 함께 만들 개발자를 찾고 있습니다. / 채용 공고 보기

### 8.6 Hero illustration

The current hero art in the mockups is a test edit of the old `slide01.jpg`
(text removed with Grok). It is navy and purple and does not match the CI
blues. Final art, in order of preference:

1. The design team's original source files for `slide01`/`slide02`, recolored
   to the CI palette by the design team.
2. If unavailable: an AI-edited version of the existing illustration,
   recolored to CI blues, at least 2560px wide for desktop, plus a separate
   portrait version for phones with no pseudo-text on any panel.

Rules for generated art: no text, no product screens, no real hardware, no
charts that could read as data. Illustration objects must not sit under the
navigation or the hero text at 390, 768, 1280, 1440, and 1920px widths.

Prompt template for option 2 (to be refined when used):
"Edit this isometric illustration: keep composition, characters, and style;
recolor to a palette of #163CCF, #1775FD, white, and light gray-blue, with
small #00C3D2 accents; remove all text and text-like marks; leave the left
45% as plain #163CCF background."

## 9. Search and comments

### 9.1 Search (Pagefind)

- Run `pagefind --site public` after `hugo` in CI.
- `<html lang="ko">`. Index only the article body (`data-pagefind-body`);
  ignore TOC, navigation, footers (`data-pagefind-ignore`). Add tag filters
  (`data-pagefind-filter="tag"`) and title/date metadata.
- Custom search UI in TypeScript using the Pagefind JS API (no Pagefind
  default UI).
- **Korean handling:** Pagefind splits on spaces and has no Korean stemmer,
  so a query like `스냅샷을` misses `스냅샷`. The UI runs the original query and
  a normalized query in which common particles are stripped from the end of
  each Korean token (은, 는, 이, 가, 을, 를, 의, 에, 에서, 으로, 로, 와, 과,
  도, 만, 까지, 부터), and merges the results, original-query hits first.
- **Acceptance list** (`tools/search_cases.txt`, at least 15 cases, each with
  the expected post): includes `ZFS`, `Lustre`, `스냅샷`, `스냅샷을`, `중복 제거`,
  `중복제거`, `이중화`, `NVMe-oF`, `씬 프로비저닝`, `재해복구`, `재해 복구`,
  `pNFS`, `CXL`, `RAID`, `백업 방식`. The builder runs these against the built
  index (a small Pagefind-in-browser check or the Pagefind API) and records
  results. Cases that fail are reported to the owner, not silently dropped.

### 9.2 Comments (giscus)

- giscus on `gluesys/tech-blog` GitHub Discussions, category "Comments",
  mapping by `pathname`, language `ko`, theme following the site theme.
- Requires enabling Discussions and installing the giscus app on the
  repository (owner action, section 13).
- Disqus and any utterances code are removed.

## 10. Build, repository layout, deploy

Repository after migration (Jekyll files removed: `_config.yml`, `_layouts`,
`_includes`, `_sass`, `css`, `js`, `Gemfile`, `.ruby-version`, `circle.yml`,
Jekyll `index.html`/`blog.html`/`posts.html`/`tags.html`/`about.html`/
`feed.xml`/`sitemap.xml`):

```
hugo.toml
content/blog/        converted and new posts
content/about.md
content/search.md
layouts/             templates, render hooks, RSS template
assets/css/          plain CSS
assets/ts/           TypeScript entry points
static/              assets/, public/, fonts/, CNAME, verification file, robots.txt
data/                tag_aliases.yaml, featured_tags.yaml, authors.yaml
tools/               convert_posts.py, verify_*.py, check_tags.py, search_cases.txt
.github/workflows/   pages.yml
README.md            how to write a post and preview locally
```

The `_posts/` source can be deleted after cutover verification passes; until
then it stays so the conversion can be re-run.

Workflow `pages.yml` on push to `master` and on pull requests:

1. Checkout.
2. Download pinned Hugo extended and Pagefind binaries, verify SHA-256.
3. `hugo --minify`.
4. `pagefind --site public`.
5. Run verification scripts (section 11) in `--ci` mode.
6. On `master` only: upload Pages artifact and deploy with
   `actions/deploy-pages`.

On pull requests the built site is uploaded as a workflow artifact for review.

Authoring for new posts: `content/blog/YYYY-MM-DD-slug.md` with front matter
`title`, `date`, `author`, `tags`, `cover`, `main`, optional `series`,
`series_order`, `summary`. New posts use the permalink
`/blog/:year/:month/:day/:slugorfilename` with `uglyURLs` for the blog section and `[frontmatter] date = [":default", ":filename"]`: the same scheme, no explicit `url` needed, and a post file `YYYY-MM-DD-slug.md` without `date` in its front matter builds as the plain file `/blog/YYYY/MM/DD/slug.html`. `tools/verify_site.py` checks that every post is such a file.
The README documents this and `hugo server` for local preview.

## 11. Verification

All checks are Python stdlib scripts under `tools/`, compare the Hugo output
in `public/` with a reference snapshot of the live site, and fail the build on
any mismatch not listed in an explicit allow-list file.

1. **Snapshot capture** (`tools/snapshot_live.py`, run once before cutover):
   fetch every live post HTML, `/feed.xml`, `/sitemap.xml`; store under
   `migration/snapshot/` on the migration branch.
2. **URLs:** every URL in the live sitemap and section 4 list exists in
   `public/`; redirects exist for `/blog/` and `/page2/` to `/page6/`.
3. **Anchors:** per post, the list of heading IDs equals the snapshot.
4. **Images:** per post, the list of `img` sources (after URL decoding)
   equals the snapshot, and every referenced file exists in `public/`.
5. **Internal links:** every internal `href` resolves to a file and, if it has
   a fragment, to an existing ID (text fragments `#:~:text=` are skipped).
6. **Footnotes:** per post, footnote definition and reference counts equal the
   snapshot (106 definitions total) and their IDs resolve.
7. **Body text:** per post, normalized visible text of the article body
   matches the snapshot; any difference is printed as a diff and must be in
   the allow-list with a reason.
8. **Feed:** `/feed.xml` parses as RSS 2.0, has 10 items with full content and
   the same item links as the live feed.
9. **Special files:** verification HTML, CNAME, favicon are byte-identical.
10. **Search:** the acceptance list in 9.1.
11. **Visual:** screenshots at 390, 768, 1280, 1920px of home, a long post
    with code and footnotes (pNFS or TrueNAS), a tag page, and search
    results, in light and dark; hero overlap checked (8.6). Done locally, not
    in CI.
12. **Accessibility basics:** visible focus, AA contrast, reduced motion
    respected, images keep their alt text.

## 12. Calls made by the designer (owner may override)

- Explicit `url:` per migrated post instead of relying on permalink patterns.
- Heading IDs pinned from the live snapshot instead of reproducing kramdown's
  ID algorithm.
- Kramdown width attributes become raw `<img>` (no Hugo image processing for
  migrated images).
- `/posts/` is the canonical archive; `/blog/` and `/pageN/` redirect to it.
- Canonical tags in `tags`, originals preserved in `legacy_tags`.
- Author emails are not displayed on the site.
- Reading time at 500 Korean characters per minute.
- Header search opens an overlay; `/search/` is the full results page.
- Dark theme included, following the OS by default.

## 13. Owner actions and open items

Needed from the owner or other teams (none block starting the build; items
2 to 6 block cutover):

1. **Design team assets (do not block cutover):** original source files for
   the `slide01`/`slide02` illustrations, the CI symbol as SVG (normal and
   reversed/white), and the CI usage rules for pairing the symbol with
   "TECH-G" (clear space, minimum size). The owner decided the site cuts over
   with fallbacks if these have not arrived, and they are swapped in later:
   - Symbol: the raster `symbol.png` cropped from the official CI logo
     (exported at 2x for sharpness), on a small light tile in dark mode.
   - Lockup rules until official ones exist: symbol at least 24px high, clear
     space around the lockup at least one quarter of the symbol height.
   - Illustration: 8.6 option 2, produced by the implementing agent through
     the Grok image delegate (as for the design-time test edit), with the
     owner reviewing the result before cutover. This is a plan task.
2. **About page content** (current page is placeholder text).
3. **Careers link** URL.
4. **Disqus:** decide whether existing Disqus comments are worth exporting
   and archiving; they will not appear under giscus.
5. **Approve GitHub changes** at cutover: enable Discussions, install giscus,
   switch Pages build source from "Deploy from a branch" to "GitHub Actions".
6. **Review the tag alias table** (5.3) once drafted.

## 14. Cutover and rollback

1. Build everything on a migration branch from `origin/master`; PR builds
   produce artifacts for review. The live site keeps running on Jekyll.
2. Right before cutover: re-run `convert_posts.py` on the latest
   `origin/master` posts, re-capture the snapshot, run all checks.
3. With owner approval: merge the PR to `master` and, immediately after,
   switch the Pages source to GitHub Actions so the Jekyll legacy build never
   runs on the Hugo tree. Keep the custom domain setting.
4. After deploy: run the URL, anchor, and feed checks against
   https://tech.gluesys.com; resubmit the sitemap in Search Console.
5. Rollback: revert the merge commit and set the Pages source back to
   "Deploy from a branch: master /". The Jekyll site returns as before.

## 15. Left to the builder

- Exact Hugo and Pagefind versions (latest stable at implementation, pinned).
- Template structure, partials, CSS file organization.
- Dark theme exact values within 8.2 rules.
- How the search acceptance list is executed.
- Snapshot storage format and whether `migration/` is removed after cutover.
- Related-posts tuning.
- Order of implementation tasks.
