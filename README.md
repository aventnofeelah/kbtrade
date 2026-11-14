# KBTrade

Django campus marketplace and Lost & Found for the KBTU community.

## Local preview

From the repository root, using the local environment prepared for this preview:

```sh
.venv/bin/python config/manage.py migrate
.venv/bin/python config/manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000/.

For a fresh machine, create a virtual environment and install the team's dependencies in `config/requirements.txt`. That original file is UTF-16 and was left unchanged. This local preview was validated with the existing Python 3.14 / Django 6.0 installation and Pillow 13.0; the team's requirements currently pin Django 6.1.3, so agree on the intended version before merging.

Optional sample data:

```sh
.venv/bin/python config/manage.py seed_demo
```

This DEBUG-only command creates eight labelled sample listings and prints a randomly generated password for `demo@kbtu.kz`. It leaves an existing demo account untouched. SQLite, uploaded media and the virtual environment are local and ignored by Git. Demo photos come from the supplied KBTrade Figma prototype. The original Figma file is not modified.

Registration still uses `@kbtu.kz` verification. In this development setup the verification code is printed in the server terminal.

## Pages

- `/` and `/home/`: combined feed, search, categories, type filters, sorting and pagination.
- `/marketplace/` and `/lost-found/`: section feeds.
- `/listings/new/`: standalone creation form; “New listing” opens the same form in a modal for signed-in users.
- `/listings/<section>/<id>/`: full listing, owner editing or email contact for signed-in students.
- `/profile/`: name and avatar editing; verified email stays unchanged.
- `/profile/listings/`: own listings, editing, hiding, status changes and confirmed deletion.
- `/profile/password/`: password change using Django authentication views.

Listings have one optional photo (maximum 5 MB). A sale requires price and condition; Lost & Found requires location and event date. Existing sale listings remain sales; lost/found listings can switch between those two types. “Available/Sold” and “Open/Resolved” describe the item; visibility separately controls whether it appears publicly. Hidden listings are visible only to their owner. Contact currently uses email, not an in-app chat.

## Implementation

The existing `users` and `posts` apps, separate `MarketItem` / `LostFoundPost` models, Django templates, forms and session authentication remain in place. Additive migrations add a user avatar, market photo/location/status and starter categories. Existing registration redirect names were corrected. No frontend framework, API rewrite or build pipeline was introduced.

Main frontend files:

- `config/users/templates/base.html`: shared navigation, footer and modal container.
- `config/posts/templates/feed.html`: campus feed and category navigation.
- `config/posts/templates/includes/listing_form.html`: shared creation/edit form.
- `config/users/templates/profile.html`: account profile.
- `config/static/css/site.css`: shared styling and responsive breakpoints.
- `config/static/js/site.js`: modal loading, conditional fields and photo preview.

## Checks

```sh
cd config
../.venv/bin/python manage.py test
../.venv/bin/python manage.py check
../.venv/bin/python manage.py makemigrations --check --dry-run
```

No commits, pushes or deployment are needed for this local preview.
