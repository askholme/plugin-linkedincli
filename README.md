# plugin-linkedincli

Stavrobot plugin wrapping [linkedin-rs](https://github.com/eisbaw/linkedin-rs) CLI for LinkedIn access.

## Setup

1. Configure the plugin with your `li_at` cookie (extracted from browser DevTools).
2. The init script authenticates automatically.

## Tools

- **auth_status** — Check session validity
- **profile_me** / **profile_view** / **profile_visit** / **profile_viewers** — Profile operations
- **feed_list** / **feed_react** / **feed_unreact** / **feed_comment** / **feed_post** — Feed operations
- **search_people** / **search_jobs** — Search
- **notifications_list** — Notifications
