# Power-Flow Feature Research

**Date:** 2026-02-06
**Status:** Brainstorming / Research Phase

---

## Executive Summary

Market research reveals strong demand for voice-to-productivity integrations. Key themes:
1. **Multi-app sync** — Users want recordings to flow to multiple destinations
2. **Smart routing** — Auto-categorize, auto-tag, route to correct project/area
3. **Calendar awareness** — Link recordings to calendar events
4. **Task extraction improvements** — Better due date parsing, priority detection
5. **Filtering/selective sync** — Don't sync everything, let users choose

---

## Research Sources

| Source | Key Findings |
|--------|--------------|
| r/heypocketai | Pocket team responsive to feature requests, active feedback forum |
| r/Notion | Voice notes to Notion is highly requested, Zapier/Make workarounds common |
| Competitor analysis | Otter, Plaud, Limitless all have integrations (Slack, Zoom, task managers) |
| Thomas Frank tutorials | 100K+ views on voice-to-Notion automation workflows |
| Notis.ai | WhatsApp-based interface, 56 languages, image transcription |

---

## Competitive Landscape

### Current Voice-to-Notion Solutions

| Tool | Approach | Pros | Cons |
|------|----------|------|------|
| **Thomas Frank Pipedream** | Whisper + ChatGPT + Notion | Free, customizable | Complex setup, requires technical skill |
| **Voices.ink** | Dedicated app | Simple, direct Notion sync | Subscription, limited features |
| **Notis.ai** | WhatsApp bot | Zero friction, multi-language | Requires WhatsApp, privacy concerns |
| **Zapier/Make DIY** | Custom automation | Flexible | Expensive at scale, fragile |
| **Power-Flow** | CLI + daemon | Robust, GTD-focused, free | Pocket-specific, technical setup |

### What Competitors Offer That We Don't (Yet)

| Feature | Otter.ai | Plaud | Notis | Power-Flow |
|---------|----------|-------|-------|------------|
| Calendar integration | ✅ | ✅ | ❌ | ❌ |
| Slack/Teams export | ✅ | ❌ | ❌ | ❌ |
| Task manager export | ❌ | ✅ (Todoist) | ❌ | ❌ |
| Custom summary prompts | ❌ | ✅ | ❌ | ❌ |
| Image transcription | ❌ | ❌ | ✅ | ❌ |
| Multi-language | ✅ | ✅ | ✅ (56) | ✅ (via Pocket) |
| Speaker diarization | ✅ | ✅ | ❌ | ✅ (via Pocket) |

---

## Feature Ideas

### Priority Framework (ICE Score)

- **Impact** (1-10): Value to users
- **Confidence** (1-10): Evidence users want this
- **Ease** (1-10): Implementation difficulty (10 = easy)
- **Score** = (Impact × Confidence) / (11 - Ease)

### Must-Have Features (Score > 15)

| Feature | Impact | Conf | Ease | Score | Notes |
|---------|--------|------|------|-------|-------|
| **Selective sync (filters)** | 9 | 9 | 7 | 20.3 | Sync only tagged recordings, date ranges, etc. |
| **Google Calendar linking** | 8 | 8 | 5 | 10.7 | Link recordings to calendar events by time overlap |
| **Todoist/Things export** | 8 | 7 | 6 | 11.2 | Extract action items directly to task manager |
| **Webhook support** | 7 | 6 | 7 | 10.5 | Real-time sync instead of polling |
| **Status notifications** | 7 | 8 | 9 | 28.0 | Desktop/mobile alerts on sync (already have macOS) |

### Nice-to-Have Features (Score 8-15)

| Feature | Impact | Conf | Ease | Score | Notes |
|---------|--------|------|------|-------|-------|
| **Project/Area routing** | 8 | 6 | 4 | 6.9 | Auto-route to Notion projects based on tags/keywords |
| **Custom summary prompts** | 7 | 7 | 5 | 8.2 | Let users define how summaries are formatted |
| **Bi-directional sync** | 6 | 5 | 3 | 3.8 | Notion edits reflect back (complex, limited value) |
| **Multi-database support** | 7 | 6 | 5 | 7.0 | Different databases for meetings vs notes vs tasks |
| **Email notifications** | 5 | 4 | 8 | 6.7 | Daily digest of synced items |
| **Web dashboard** | 6 | 5 | 3 | 3.8 | Visual sync history and management |

### Future Consideration (Score < 8)

| Feature | Impact | Conf | Ease | Score | Notes |
|---------|--------|------|------|-------|-------|
| **Slack integration** | 6 | 4 | 4 | 3.4 | Post summaries to Slack channels |
| **Linear/Jira export** | 5 | 3 | 4 | 2.1 | Dev-focused, niche audience |
| **Obsidian support** | 6 | 4 | 6 | 4.8 | Growing audience, markdown-native |
| **Apple Reminders export** | 5 | 4 | 5 | 3.3 | Native Apple ecosystem |
| **Voice command setup** | 4 | 3 | 3 | 1.5 | "Hey Siri, sync my Pocket" |

---

## User Personas & Their Needs

### 1. The GTD Practitioner
- **Goal:** Everything → Inbox → Process → Organize → Do
- **Pain:** Manual copy-paste breaks flow
- **Wants:** Auto-sync to inbox, then they process manually
- **Power-Flow fit:** ✅ Perfect (recording-centric design)

### 2. The Meeting-Heavy Professional
- **Goal:** Capture meetings, extract action items, assign tasks
- **Pain:** Action items get lost, no follow-through
- **Wants:** Auto-extract tasks to Todoist/Asana, calendar linking
- **Power-Flow fit:** Partial (need task manager export)

### 3. The Thought Capturer
- **Goal:** Record random thoughts, ideas, notes throughout day
- **Pain:** Ideas scattered across devices and apps
- **Wants:** One place for all thoughts, searchable
- **Power-Flow fit:** ✅ Good (full transcript + summary)

### 4. The Content Creator
- **Goal:** Turn voice memos into blog posts, newsletters
- **Pain:** Transcription → editing → publishing is tedious
- **Wants:** Draft generation, formatting, publishing workflow
- **Power-Flow fit:** Partial (need custom prompts, export formats)

---

## Recommended Roadmap

### Phase 1: Filtering & Notifications (Low effort, high impact)
1. **Selective sync by tags** — Only sync recordings with specific tags
2. **Date range filters** — Sync only last N days
3. **iOS/Android notifications** — Via Pushover or native (if possible)

### Phase 2: Integrations (Medium effort, high demand)
1. **Google Calendar linking** — Match recordings to events by time
2. **Todoist/Things export** — Send action items directly
3. **Webhook trigger** — For real-time integrations

### Phase 3: Smart Routing (Higher effort, differentiation)
1. **Auto-categorization** — Route to different databases by content
2. **Custom prompts** — User-defined summary formats
3. **Multi-destination** — Same recording to multiple places

---

## Open Questions

1. Does Pocket plan to offer webhooks? (Would change our architecture)
2. What's the Pocket API rate limit? (Affects polling frequency)
3. Is there demand for a GUI? (Or is CLI sufficient for target audience)
4. Should we support other voice tools? (Otter, Plaud, etc.)

---

## Sources Consulted

- Reddit: r/heypocketai, r/Notion, r/PlaudNoteUsers, r/zapier
- Product sites: heypocket.com, otter.ai, plaud.ai, notis.ai, voices.ink
- Tutorials: thomasjfrank.com (Ultimate Brain voice notes)
- Review sites: howtogeek.com, fritz.ai
- Automation platforms: Zapier, Make, Pipedream

---

*This document is for brainstorming purposes. Features listed are not commitments.*
