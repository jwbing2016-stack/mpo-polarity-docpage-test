# Isolated WordPress sync

Branch: wordpress-sync-test. This workflow does not trigger DEV/Blogger or alter main.
Source: article.md, copied unchanged from jwbing2016-stack/mpo-polarity-reference/main/README.md.
Existing target: site 258218432, post 4. wordpress-sync.json maps sources to existing post IDs.
No fallback creation. A missing/wrong/deleted post fails. Additional mapped articles can be processed sequentially; new posts must be created and mapped explicitly.

## Authorization
WordPress.com OAuth authorization for GitHub Actions is separate from the chat connector.
Register an application through https://developer.wordpress.com/apps/ and authorize only the test site, requesting the posts scope.
Use the authorization-code flow described at https://developer.wordpress.com/docs/api/oauth2/.
Store the resulting token ONLY as repository Actions secret WORDPRESS_ACCESS_TOKEN; never commit credentials.
Scope and actual returned expiration/renewal behavior must be checked during authorization. Handle expired/revoked tokens by stopping with an error and reauthorizing.

## Run
pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/sync_wordpress.py --dry-run
WORDPRESS_ACCESS_TOKEN must exist in the environment for a real update.
Push an article.md change on wordpress-sync-test to run; all other platform branches stay unchanged.
An absent secret produces a clear validation-only warning; a green validation run alone is not proof of publication.
A valid token triggers preflight target checks, update, then authenticated readback checking text and links.
The public permalink must be checked for the first real source-change test.

## Status 2026-10-27
Workflow prepared; runtime authorization and push-to-public-page verification pending.
Free WordPress site; no purchases made. Three backlink spreadsheets unchanged.
