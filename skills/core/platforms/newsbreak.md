# NewsBreak

NewsBreak pays on article page views and distributes by its own feed algorithm. Views are the only score.

## How articles reach NewsBreak
- Most WordPress sites send posts through the **NewsBreak Feed for WordPress** plugin. Its feed (`/feed/newsbreak`) includes **only** posts flagged "Send this post to the NewsBreak feed" (post meta `_nbfw_send_to_newsbreak = "1"`). An unflagged post publishes fine on the site and **never reaches NewsBreak**: a total loss for that article, with no error anywhere.
- `schedule_article` sets the flag on every post for a NewsBreak site and reports `newsbreak_flag`. If it says **NOT SET** on a site that uses the plugin, put it at the top of the run summary every time until fixed. Never work around it (no direct database writes, no browser clicking through every post).
- Galleries don't earn on NewsBreak. NewsBreak sites are **articles only**; never schedule galleries there.

## What gets warned, throttled or terminated
NewsBreak's own rules, plus what has actually happened to sites:
- **Stale presented as current** (see the shared currency rule): the single biggest cause of warnings and removals.
- False, misleading or unverified claims, rumor and hearsay, unsupported accusations. Publishers must fact-check their own content.
- **Clickbait** is banned outright. The headline can be intense; it can't promise what the article doesn't deliver.
- Opinion or satire must say so in the headline.
- Claims or quotes without proper sourcing; facts that could be challenged need attribution.
- Uncredited or unlicensed images; misleading crops; edits that change a photo's meaning; undisclosed composites.
- Plagiarism and copied content. Original reporting is preferred.
- One uniform headline formula at scale (the em-dash formula especially): a documented termination reason.
- Spam, impersonation, coordinated inauthentic behavior.
- Hate, violence, harassment, self-harm, adult content, gore without news value, privacy violations.
- The site must have terms of use, a privacy policy and contact information.

Consequences run from lower distribution to removal of articles to account termination. Two of the founding network's sites were terminated; treat every rule here as hard.

## Reading the numbers
- An article NewsBreak didn't make live (its status isn't live, or it was rejected) is a **distribution problem**, not a headline problem. Report it; don't learn from it.
- Never judge by click-through rate. A big view count means NewsBreak pushed the article.
- The latest month always looks low (less time to collect views). Never call that a decline.
