# Search fields for every article

Google's own guidance (October 2026): AI-assisted articles are fine when they are accurate, sourced, bylined and useful; titles, descriptions, alt text and structured data should be reviewed like the article. These fields are written from the checked article, never invented.

- **seo_title** (50–60 characters): the phrase a reader would search, then the specific: "Medicare Part B Premium 2027: $206.50 a Month". It may differ from the display headline, but must say the same thing. No clickbait, no ALL CAPS, no "you won't believe", no year unless the story is about that year.
- **meta_description** (120–160 characters): who it affects, the number, and why it matters, as one or two plain sentences. It's the snippet under the title in Google, and also the WordPress summary.
- **slug** (3–6 lowercase words, hyphenated): the words a person would type: `medicare-part-b-premium-2027`. No dates unless they're part of the subject, no stop words, never changed after publishing.
- **focus_keyword**: the one phrase the article answers best.
- **tags**: at most 3, from the site's existing tag list (the categories carry the topic; tags group the same subject across articles).

The Yeez WordPress plugin puts these into the site's SEO plugin (Yoast, Rank Math or SEOPress), marks the article as a news article for Google, adds it to the Google News sitemap and tells Bing the moment it goes live. If `schedule_article` says the fields weren't saved, the plugin isn't installed: run `site_seo_status` and tell the buyer.
