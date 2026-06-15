---
name: ai-daily-poster
description: "Generate and push an AI daily news poster to a WeCom group. Produces an 800x1600 vertical poster with deep-blue/gold styling, real-time Lanzhou weather, traffic restrictions, and 5 categorized news items (AI, Real Estate, Gansu Local, International, Finance). Use when the user asks to push daily AI news, generate a news poster, send daily report, or set up the daily 9:05 AM automation."
agent_created: true
---

# AI Daily News Poster

## Overview

Generate a polished 800×1600 vertical poster with real-time data and push it to a designated
WeCom (WeChat Work) group chat. The poster includes: date, weather (auto-translated to Chinese),
city-specific traffic restrictions, an inspirational quote, and 5 categorized news cards.

**Fully customizable**: logo/brand name, background image, news categories & sources,
WeCom target group, city, colors, and quotes — all editable in the script. See the
[Customization Guide](#customization-guide) for step-by-step instructions.

## Quick Start

To generate and push the poster immediately:

```powershell
& "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe" "scripts/generate_poster.py"
```

The script handles everything: weather fetching, news scraping, poster rendering, and WeCom push.
It outputs to `poster_today.png` in the current directory.

**First-time users**: read the [Customization Guide](#customization-guide) below to:
- Replace the logo with your brand name
- Change news categories to match your industry
- Set your own WeCom webhook
- Swap the background image

## Script Behavior

The poster generation script (`scripts/generate_poster.py`, v5.6) is self-contained and performs:

1. **Weather** - Fetches from wttr.in API, auto-translates to Chinese
2. **News** - Scrapes 5 categories from multiple sources:
   - AI (txtmix.com + neican.ai)
   - Real Estate (Sogou search)
   - Gansu/Lanzhou Local (Sogou search)
   - International (Sogou search)
   - Finance (Sogou search)
3. **Traffic restrictions** - Calculates Lanzhou rules based on weekday
4. **Poster rendering** - Pillow-based composition: deep-blue gradient, gold titles,
   semi-transparent dark cards, 82px bold main title with multi-layer stroke.
   Cards auto-resize: titles and summaries wrap by pixel width (not character count),
   card height adapts to content, canvas height expands beyond 1600px as needed.
5. **WeCom push** - Sends the image via webhook to the target group

## Fallback Mechanism

When any news source fails (e.g. Sogou anti-scraping triggers), the script falls back to
a 3-group x 5-item rotation library keyed by `(day + month) % 3`, ensuring different
content each day while maintaining the 5-category structure. Each fallback group contains
exactly 1 item per category.

## Quality Filters

The script applies strict quality filtering to news titles:
- Rejects date-prefixed summary pages
- Rejects navigation/description text
- Rejects emoji-prefixed aggregation titles
- Rejects numeric bullet-point items
- Requires 6+ Chinese characters in title
- Caps title at 35 characters, summary at 80 characters
- Splits title/summary on colon only when colon appears within first 15 chars

## Daily Automation

To set up the daily push, create a WorkBuddy automation with:
- **Schedule**: `FREQ=DAILY;BYHOUR=9;BYMINUTE=5`
- **Prompt**: Run the script via the PowerShell command above
- **Working directory**: The project workspace directory

The user's computer powers on at 9:00 AM; 9:05 allows time for system startup.

## Customization Guide

The script is designed to be modified for different brands and content needs. Below are the
key customization points — all in `scripts/generate_poster.py`.

### 1. Change the Logo / Main Title

**Line ~661**: change the `title` variable.

```python
# Default: AI 资讯日报
title = "AI 资讯日报"

# Example: Your brand name
title = "贝壳找房 · 每日速递"
title = "枔家早报"
title = "XX公司晨报"
```

The title uses **82px bold font** with a gold gradient stroke effect. Keep it under 8 Chinese
characters for best visual results. If you need a longer title, reduce font size on line ~659
(`f_title = find_font(82, bold=True)` — try 60-72).

### 2. Change the Background Image

Replace `assets/bg_mountain.png` with your own 800×1600 image. Any PNG/JPG works.
The script automatically applies a dark semi-transparent overlay for readability.

To generate a custom background with AI:
> "Generate an 800x1600 vertical poster background image for [your brand], dark tone,
> professional style"

### 3. Change News Categories

The script fetches 5 categories: AI, Real Estate, Gansu Local, International, Finance.
To change which categories appear:

**A. Modify the `fetch_news()` function** — add/remove category blocks.
Each block follows this pattern:

```python
# ====== YOUR CATEGORY ======
print("  🔍 抓取YOUR_CATEGORY新闻...")
time.sleep(2)
for kw in ["YOUR+KEYWORD", "ANOTHER+KEYWORD"]:
    # ... Sogou search logic ...
    if any(kw in clean for kw in ['your', 'match', 'keywords']):
        your_news.append({"title": title, "summary": summary, "source": "YOUR_SOURCE"})
```

**B. Update the `categories` list** on line ~418 to match your new structure:

```python
categories = [
    ("YOUR_CAT_1", cat1_news),
    ("YOUR_CAT_2", cat2_news),
    # ... add/remove as needed
]
```

**C. Update fallback news** in `get_fallback_news()` (line ~526) to match your categories.

### 4. Change News Sources

Instead of Sogou search, you can plug in any news API:

```python
# Replace Sogou block with your API:
r = requests.get("https://your-news-api.com/latest", headers={"Authorization": "Bearer XXX"})
for article in r.json()["articles"]:
    your_news.append({"title": article["title"], "summary": article["desc"], "source": "API"})
```

### 5. Change WeCom Webhook Target

**Line ~783**: update the `webhook_url` variable with your group's webhook key.

```python
webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE"
```

Get your webhook key from: WeCom group → Group Settings → Group Robot → Add Robot → Copy URL.

### 6. Change Inspirational Quotes

**Line ~593**: replace the `quotes` list with your own.

```python
quotes = [
    "你的第一条金句",
    "你的第二条金句",
]
```

### 7. Change Weather City

**Line ~582**: update `city` from "兰州" to your city.

```python
weather_info = {
    "city": "兰州",   # ← change this
    ...
}
```

Also update the `fetch_weather()` call on line ~570.

### Quick Customization Checklist

| What | Where (line) | Difficulty |
|------|-------------|------------|
| Logo / Title | ~661 | 1 min |
| Background image | `assets/bg_mountain.png` | 1 min |
| WeCom webhook | ~783 | 1 min |
| City name | ~582, ~570 | 1 min |
| Quotes | ~593 | 2 min |
| News categories | ~104-524, ~526-559 | 15-30 min |
| News sources | ~121-342 | 15-30 min |
| Colors / fonts | ~609-618, ~15-34 | 5-10 min |

After making changes, test with:
```powershell
& "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe" "scripts/generate_poster.py"
```

## Poster Layout (Reference)

```
+----------------------------------+
|  Background: mountain dawn       |  720x1280 bg_mountain.png
|  (semi-transparent overlay)      |
|                                  |
|    Main Title (centered)         |  82px bold, gold #FFD700, multi-stroke
|                                  |
|  Date / Weather / Restriction    |  Left-aligned below title, vertical stack
|                                  |
|  "Inspirational quote..."        |  20px centered
|  ------------------------------  |  Divider line (tight spacing)
|                                  |
|  (1) Category 1 Title            |  Number: 48px gold
|      Brief summary text...       |  Title: 26px bold
|                                  |  Summary: 18px bright white
|  (2) Category 2 Title            |  Card: dark semi-transparent (alpha=180)
|      ...                         |
|  ...                             |
|  (5) Category 5 Title            |
|      ...                         |
+----------------------------------+
```

## Bundled Resources

### scripts/generate_poster.py
The complete poster generation script (v5.6). Self-contained - requires only
Python 3.13+ with Pillow and requests installed. Handles all data fetching,
poster rendering, and WeCom push in one execution.

### assets/bg_mountain.png
720x1280 background image: mountain climber at dawn with golden sunlight and cloud sea.
Generated via AI image generation. Replace to change the poster theme.
