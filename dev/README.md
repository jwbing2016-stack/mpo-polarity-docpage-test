# DEV publishing

Repository: `jwbing2016-stack/mpo-polarity-docpage-test`, branch `platform-sync-test`.

Add one new Markdown file under `dev/articles/` and commit it. Begin with `# Article title`, then the body with clickable Cablefam links. Use a unique, stable lowercase filename such as `lc-fiber-cable-ordering-guide.md`. The `DEV article sync` Action creates a new DEV article and records its ID in `dev/publish-state.json`. Editing that same file updates that same ID. Unchanged articles are checked without sending publication updates.

The existing MPO and LC posts are mapped to IDs `4903363` and `5022405`; do not create them again. Their files were copied from the existing DEV Markdown for this migration. The original local LC source remains unchanged. Root `article.md` is now the legacy Blogger source, not the DEV publishing entry.

Only DEV is called by the new workflow. It reuses the existing `DEV_API_KEY` repository Secret and verifies the account is `cablefam_fiber_optic`. Do not copy credentials into files. The old workflow's live DEV step is removed; Blogger code, state and OAuth are unchanged.

After a commit, open the `DEV article sync` Action once and check the resulting article URL and website links. Keep the bot's saved state commit. If a request fails or the state cannot be pushed, inspect the existing DEV articles and the `dev-publication-state` workflow artifact before retrying. Matching titles are recovered only when content agrees; conflicting titles, wrong owners and external edits stop rather than create replacements. Renaming/deleting files does not delete remote articles.

Checks: `node --test tests/sync_dev.test.mjs`; authenticated read-only verification: `node scripts/sync_dev.mjs --check`. New article creation has unit coverage; the first future real new article must still be checked on DEV. Do not publish dummy articles to fill that gap.
