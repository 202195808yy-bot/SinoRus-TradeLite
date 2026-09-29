# TradeHub — a collaboration platform for Russia–China cross-border trade

**Language:** [Русский](README.md) · [English](README.en.md)

Course project for the discipline **“Web application development with
Python”**.

A Django web application implementing the client side of the platform: it
brings together the scattered information and tasks of the several parties to
a deal (seller, buyer, carrier, customs broker) onto a single timeline.

## Development stage

| Stage | Content | Status |
|---|---|---|
| — | Create the Django project; page list with addresses and descriptions; routes and view prototypes; publish to git | done |
| 1 | Domain: overview of the area and entity list (document, 2 languages) | done |
| 2 | Application page descriptions (document) | done |
| 3 | Application models (document, 2 languages) | done |
| 4 | Application page templates | — |
| 5 | Application users | — |

## Mobile client

In parallel with the web version, a mobile client of the same platform
(React Native) is being developed for the discipline **“Mobile application
development technologies”**. Its first stage — the domain description and the
functional requirements list — is complete; the bilingual document is
provided in `docs/`.

The mobile client does not duplicate the web version; it serves “on the
spot” actions: confirmations, milestone marks, document capture, code
scanning and offline work. Correspondence of mobile modules to web modules:

| Module | Name | Requirements | Web module |
|---|---|---|---|
| FM0 | Common screens and navigation | 3 | M0 |
| FM1 | Authentication and profile | 4 | M1 |
| FM2 | Home screen and tasks | 4 | M8 |
| FM3 | Requests and offers | 4 | M3 |
| FM4 | Orders and fulfilment | 5 | M4 |
| FM5 | Documents and scanning | 5 | M6 |
| FM6 | Logistics and tracking | 4 | M5 |
| FM7 | Settlements and reconciliation | 4 | M10 |
| FM8 | Messages and translation | 4 | M7 |
| FM9 | Notifications and push | 3 | M8 |
| FM10 | Offline mode and synchronisation | 4 | — |
| FM11 | Settings and administration | 4 | M11 |
| | **Total** | **48** | |

Of the 48 requirements, 25 are high priority, 19 medium and 4 low. Twelve
non-functional requirements are defined as well. Module FM10 has no web
counterpart: working without a network and the queue of deferred operations
are properties of the mobile client specifically.

The same document is also available in markdown in three languages:
`docs/mobile/mobileapp.ru.md`, `docs/mobile/mobileapp.zh.md` and
`docs/mobile/mobileapp.en.md`. The markdown versions and the `.docx` files
are built from a single data source, so their tables and numbers match.

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Apply migrations
python manage.py migrate

# 3. Run the development server
python manage.py runserver
```

The application is available at <http://127.0.0.1:8000/>,
the admin panel at <http://127.0.0.1:8000/admin/>.

## Project structure

```
course_project/
├── manage.py                  project management entry point
├── requirements.txt           dependencies
├── .gitignore
├── README.md                  Russian README
├── README.en.md               this file
├── docs/
│   ├── pages.ru.md            page list, Russian (generated)
│   ├── pages.zh.md            same in Chinese (generated)
│   ├── pages.en.md            same in English (generated)
│   ├── Предметная_область_и_сущности.docx      stage 1 document, ПЗ (32 pp., 56 entities, 9 classes)
│   ├── Предметная_область_и_сущности_CN.docx   same in Chinese (26 pp.)
│   ├── Описание_страниц_приложения.docx        stage 2 document (ПЗ, 28 pp.)
│   ├── Модели_приложения.docx                  stage 3 document, ПЗ (29 pp., 52 models, 23 constraints)
│   ├── Модели_приложения_CN.docx               same in Chinese (28 pp.)
│   ├── 移动应用开发课设_学科领域与功能需求（俄文）.docx   mobile client, ПЗ (36 pp., 48 requirements)
│   ├── 移动应用开发课设_学科领域与功能需求（中文）.docx   same in Chinese (30 pp.)
│   └── mobile/                mobile client document in markdown, three languages
│       ├── mobileapp.ru.md    full document, Russian
│       ├── mobileapp.zh.md    same in Chinese
│       ├── mobileapp.en.md    same in English
│       └── figures_{ru,zh,en}/  figures for the corresponding language version
├── tools/
│   ├── check_routes.py        page registry vs Django routes check
│   ├── check_i18n.py          registry translation completeness check
│   ├── smoke_test.py          smoke test: request every page
│   └── gen_docs.py            generates docs/pages.{ru,zh,en}.md
├── tradehub/                  project configuration
│   ├── settings.py
│   ├── urls.py                root URLconf
│   ├── asgi.py
│   └── wsgi.py
├── portal/                    course project application
│   ├── pages.py               SINGLE PAGE REGISTRY (43 entries)
│   ├── urls.py                routes grouped by modules M0..M11
│   ├── views.py               view prototypes
│   ├── context_processors.py  module navigation
│   ├── models.py              application models: 52 models, 9 classes (stage 3)
│   ├── admin.py               model registration, tabular inlines
│   ├── tests.py               20 model tests: numbering, properties, constraints
│   ├── management/commands/seed_demo.py   idempotent demo data loader
│   └── migrations/
├── templates/
│   ├── base.html              base template
│   └── portal/
│       ├── index.html         landing page
│       ├── page.html          universal prototype page template
│       └── dashboard.html     execution dashboard
└── static/
    └── css/style.css          prototype styles
```

## Single page registry

The key architectural decision is the `portal/pages.py` module. It holds the
single source of truth about every application page and serves three
consumers:

* `portal/urls.py` — route construction;
* `portal/views.py` — view prototypes;
* `docs/pages.{ru,zh,en}.md` and the “Application page descriptions”
  document — page descriptions.

Because of this, the page list cannot diverge between the code, the
repository and the explanatory note.

Each registry entry stores the page title, purpose and content in three
languages (Russian, Chinese, English); route parameter descriptions are
dicts keyed by language. Values are read through the helpers `title_of()`,
`purpose_of()`, `content_of()`, `params_of()` and `module_name()`, so adding
a fourth language requires no changes in the consumers.

## Application models

Stage 3 implements the data models in `portal/models.py`: 52 Django models
cover the 56 domain entities (9 classes). Four entities are implemented not
as tables but as fields and value dictionaries: product characteristics as
the `Good.attributes` JSON field, the role as the `Membership.Role`
dictionary, a file (media) as `FileField`s plus the `Attachment` model, and
a glossary term as a static interface reference.

| Item | Count | Location |
|---|---|---|
| Models | 52 | `portal/models.py` |
| Fields (excluding PK) | 394 | same |
| Integrity constraints | 23 | model `Meta.constraints` |
| Application-level indexes | 11 | model `Meta.indexes` |
| Computed properties | 9 | model properties |
| Auto-numbered documents | 7 | `DocNumberMixin` |

Shared mechanisms: the `TimeStampedModel` abstract model with time stamps,
`DocNumberMixin` for numbers like `RFQ-2026-0001` (base-class order matters —
`class Rfq(DocNumberMixin, TimeStampedModel)`), `DecimalField` for money,
`TextChoices` dictionaries, and a Russian `verbose_name` on every field.

```bash
python manage.py migrate           # create 53 tables
python manage.py seed_demo         # demo deal chain
python manage.py test portal       # 20 model tests
```

The `seed_demo` command is idempotent (a second run creates no duplicates)
and builds an end-to-end example: RFQ → quote in two versions → order with
eight milestones → shipment → transport with waybill and track points →
incident → document set → soon-expiring certificate → dialog with
translation → task → statement, payment and reconciliation. Demo users:
`ivanov`, `wang`, `petrov`, `admin`, password `tradehub-demo-2026`.

The stage document is `docs/Модели_приложения.docx` (ПЗ, 29 pp.) with a
Chinese counterpart `docs/Модели_приложения_CN.docx` (28 pp.); every table
in the document is built from ORM metadata, so it cannot drift apart from
the code.

## Application modules

| Code | Module | Pages |
|---|---|---|
| M0 | Common pages | 6 |
| M1 | Enterprise and account | 4 |
| M2 | Goods | 3 |
| M3 | RFQs and quotes | 5 |
| M4 | Orders | 4 |
| M5 | Logistics and border crossings | 4 |
| M6 | Documents and compliance | 4 |
| M7 | Bilingual communication | 2 |
| M8 | Tasks and reminders | 3 |
| M9 | Analytics | 3 |
| M10 | Settlements and reconciliation | 2 |
| M11 | Administration | 3 |
| | **Total** | **43** |

## Verifying the project

```bash
python manage.py check          # configuration check
python tools/check_routes.py    # page registry vs routes
python tools/check_i18n.py      # three-language translation completeness
python tools/smoke_test.py      # smoke test: request every page
python tools/gen_docs.py        # refresh docs/pages.{ru,zh,en}.md
```

## Domain boundaries

The platform takes the position of a “trade collaboration layer” and
deliberately does not perform:

1. payment operations — only recording payment state and party confirmations;
2. customs clearance and certification — only collection, checks and reminders;
3. issuing a final compliance judgement — only facts and a list of missing
   documents;
4. collecting personal data unrelated to business necessity.
