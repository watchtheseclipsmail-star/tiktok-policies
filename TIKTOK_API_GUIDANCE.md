# TikTok API Application Guidance

## Overview
TikTok requires a Terms of Service (ToS) and Privacy Policy for API app approval, even for personal projects. You do **not** need a full commercial application; instead, create simple, honest documents that describe your personal use case.

## Key points for TikTok's review
1. **Honesty is critical**: Misrepresenting your app can lead to rejection or ban.
2. **Personal use is acceptable**: TikTok allows automation for personal accounts if you comply with their API terms.
3. **Privacy & data handling**: Clearly describe what data you collect, how you store it, and that you don't sell user data.
4. **Attribution**: Always credit the original streamer/creator when reposting clips.

## What to fill in the TikTok form

### Application Name
Example: `StreamClipAutoReposter` or `Personal Clip Processor`

### Application Description
```
A personal tool that automatically finds and downloads clips from Twitch streamers, 
adds captions using speech-to-text, reformats them to vertical video (9:16), and 
uploads them to my personal TikTok account for archival and sharing. 

No user data is collected beyond my own Twitch and TikTok credentials. Videos are 
sourced from public Twitch clips with full attribution to the original streamers.
```

### Use Case / Intended Purpose
Select: **Personal/Private Use** or **Content Creation** (depending on TikTok's options)

Describe:
```
Automating the reposting of public Twitch clips I curate to my personal TikTok account. 
This is for personal curation and archival, not commercial redistribution.
```

### Data & Privacy
Emphasize:
- Only your own TikTok credentials are used (no third-party users).
- Videos are sourced from public clips with creator attribution.
- No user data is collected or shared with third parties.
- All operations are local or use TikTok's official API only.

## Files in this directory

- **TIKTOK_TERMS_OF_SERVICE.md** — Template Terms of Service for personal use.
- **TIKTOK_PRIVACY_POLICY.md** — Template Privacy Policy for personal use.

Copy these to your own domain or host them on a simple GitHub Pages site, 
then provide the URLs in the TikTok app form.

## Steps to register an app on TikTok Developer Portal

1. Go to [https://developer.tiktok.com](https://developer.tiktok.com)
2. Log in with your TikTok account (or create one if needed).
3. Navigate to **My Apps** → **Create an app**
4. Fill in:
   - **App Name**: e.g., "StreamClipAutoReposter"
   - **App Category**: "Other" or "Utility" (if available)
   - **Platform**: "Web" or "Mobile" (or both)
5. In the next section, provide:
   - **Terms of Service URL**: Link to your hosted `TIKTOK_TERMS_OF_SERVICE.md`
   - **Privacy Policy URL**: Link to your hosted `TIKTOK_PRIVACY_POLICY.md`
   - **App Description** (as above)
   - **Intended Use**: Personal automation for clip reposting
6. Submit for review. TikTok typically responds within 3–7 working days.

## Hosting your policies

Simple options:
- **GitHub Pages** (free): Create a repo, add the `.md` files, enable Pages, and share the raw URLs.
- **Notion/Medium** (free): Copy the policy text into a Notion page and share the public link.
- **Any web host**: Upload `TIKTOK_TERMS_OF_SERVICE.md` and `TIKTOK_PRIVACY_POLICY.md` to your web server.

GitHub Pages example:
1. Create a repo `tiktok-policies` (or similar).
2. Add the `TIKTOK_TERMS_OF_SERVICE.md` and `TIKTOK_PRIVACY_POLICY.md` files.
3. Enable GitHub Pages (Settings → Pages → Source: main branch).
4. URLs will be:
   - `https://yourusername.github.io/tiktok-policies/TIKTOK_TERMS_OF_SERVICE.md`
   - `https://yourusername.github.io/tiktok-policies/TIKTOK_PRIVACY_POLICY.md`

## After approval

Once approved, you'll receive:
- **Client ID**
- **Client Secret**
- Access to the **Content Publishing API** (or user OAuth)

You can then set these in your environment and use the prototype's `--tiktok` flag.

## Important: Compliance reminders

- **Always attribute the original creator** in the clip's caption or description.
- **Do not claim ownership** of the clips you repost.
- **Monitor for DMCA takedown requests** (keep a process to remove videos on demand).
- **Respect TikTok's and Twitch's terms**: Do not violate rate limits or spam.
- **Consider streamer consent**: Ideally, get permission from streamers before reposting their clips at scale.

