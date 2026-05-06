# plugin-linkedincli

Stavrobot plugin wrapping the private `askholme/linkedin-rs-private` `linkedin-cli` for LinkedIn access.

## Setup

1. Configure the plugin with your `li_at` cookie (extracted from browser DevTools).
2. To use `feed_list` with recent sorting, also configure `jsessionid`, `li_gc`, and `bcookie`, or provide `cookies_file`.
3. The init script authenticates automatically.

## Tools

- **auth_status** — Check session validity
- **profile_me** / **profile_view** / **profile_visit** / **profile_viewers** — Profile operations
- **feed_list** — Read feed, including `sort=recent` when web cookies are configured
- **search_people** / **search_jobs** — Search
- **notifications_list** — Notifications

## Build

`./build.sh` clones `askholme/linkedin-rs-private` with `gh`, builds it in Docker, and extracts `bin/linkedin-cli`.
