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
| 4 | Application page templates | done |
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

### Environment requirements

The Django 4.2 branch officially supports Python 3.8–3.12. The project
nevertheless runs on newer versions — up to 3.14: the incompatibility in
template context copying is worked around in place, without touching
`site-packages` and without changing `requirements.txt` (see
`portal/compat.py`).

| Python | Django | State |
|---|---|---|
| 3.8–3.12 | 4.2.30 | stock behaviour, the shim stays off |
| 3.13 | 4.2.30 | stock behaviour, the shim stays off |
| 3.14 | 4.2.30 | works through `portal/compat.py` |

The shim is enabled in `PortalConfig.ready()`, and only when the native
implementation is genuinely broken: the check is by fact, not by version
number — an empty context is copied. If copying succeeds, nothing is
touched and Django's behaviour stays as shipped.

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
│   ├── Описание_страниц_приложения.docx        stage 2 document, ПЗ (31 pp., 43 pages, 12 modules)
│   ├── Описание_страниц_приложения_CN.docx     same in Chinese (27 pp.)
│   ├── Модели_приложения.docx                  stage 3 document, ПЗ (29 pp., 52 models, 23 constraints)
│   ├── Модели_приложения_CN.docx               same in Chinese (28 pp.)
│   ├── Представления_и_данные.docx             stage 4 document, ПЗ (26 pp., 43 pages, 45 models)
│   ├── Представления_и_данные_CN.docx          same in Chinese (26 pp.)
│   ├── 移动应用开发课设_学科领域与功能需求（俄文）.docx   mobile client, ПЗ (36 pp., 48 requirements)
│   ├── 移动应用开发课设_学科领域与功能需求（中文）.docx   same in Chinese (30 pp.)
│   └── mobile/                mobile client document in markdown, three languages
│       ├── mobileapp.ru.md    full document, Russian
│       ├── mobileapp.zh.md    same in Chinese
│       ├── mobileapp.en.md    same in English
│       └── figures_{ru,zh,en}/  figures for the corresponding language version
├── tools/
│   ├── check_routes.py        page registry vs Django routes check
│   ├── check_data.py          page data registry vs page registry check
│   ├── check_i18n.py          registry translation completeness check
│   ├── check_lang.py          translation completeness (labels, enums, references)
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
│   ├── context_processors.py  module navigation and interface language
│   ├── i18n.py                language switching: interface texts, helpers
│   ├── labels.py              translation dictionary: labels, enumerations,
│   │                          reference values (501 entries, ru→zh/en)
│   ├── admin_labels.py        panel label dictionary (154 entries, ru→zh/en)
│   ├── admin_i18n.py          lazy ORM label translation for /admin/
│   ├── compat.py              Python 3.14 shim: template context copying
│   │                          (Django 4.2 + Python 3.14)
│   ├── middleware.py          language selection: ?lang= / /lang/<code>/ → session
│   ├── langcheck.py           self-check: labels, choices, reference values,
│   │                          panel labels
│   ├── datasets.py            SINGLE PAGE DATA REGISTRY: context providers
│   ├── models.py              application models: 52 models, 9 classes (stage 3)
│   ├── admin.py               model registration, tabular inlines
│   ├── tests.py               23 model tests: numbering, properties, constraints
│   ├── tests_views.py         17 page and data tests (stage 4)
│   ├── tests_i18n.py          80 tests: switching, translation, purity
│   ├── tests_compat.py        9 tests: context copying, Python 3.14 shim
│   ├── templatetags/          template filters (tr, fmt)
│   ├── management/commands/seed_demo.py   idempotent demo data loader
│   └── migrations/
├── templates/
│   ├── base.html              base template
│   ├── admin/
│   │   ├── base_site.html     panel header: language switcher
│   │   └── _lang_switch.html  the switcher itself (RU · 中文 · EN)
│   └── portal/
│       ├── index.html         landing page
│       ├── page.html          universal page template
│       ├── _blocks.html       data block rendering: kpi, tables, fields
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

The stage 2 document is `docs/Описание_страниц_приложения.docx` (ПЗ, 31
pp., 43 pages, 12 modules) with a Chinese counterpart
`docs/Описание_страниц_приложения_CN.docx` (27 pp.). The page tables are
built directly from the registry, so the list in the document and in the
code agree by construction.

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
python manage.py test portal       # 129 tests: models, pages, languages
```

The `seed_demo` command is idempotent (a second run creates no duplicates)
and builds an end-to-end example: RFQ → quote in two versions → order with
eight milestones → shipment → transport with waybill and track points →
incident → document set → soon-expiring certificate → dialog with
translation → task → statement, payment and reconciliation.

Demo users, all with the password `tradehub-demo-2026`:

| Login | Role | Access |
|---|---|---|
| `admin` | administrator | `/admin/` panel (is_staff, is_superuser) |
| `ivanov` | procurement, Russian company | application pages |
| `wang` | supplier, Chinese company | application pages |
| `petrov` | carrier operator | application pages |

The command sets the administrator password on creation and restores it if
the record was left with an empty password (that is how an earlier version
of the command created it, which made `/admin/` inaccessible).

The stage document is `docs/Модели_приложения.docx` (ПЗ, 29 pp.) with a
Chinese counterpart `docs/Модели_приложения_CN.docx` (28 pp.); every table
in the document is built from ORM metadata, so it cannot drift apart from
the code.

## Application page templates

Stage 4 wires the pages to the models. The single data registry
`portal/datasets.py` maps every page to a context provider function
`provider(request, **kw)` that returns a set of blocks (`kpi` — metrics,
`table` — a table with link and badge cells, `fields` — a field card,
`list` — a short list). The universal template
`templates/portal/_blocks.html` renders these blocks, so the same markup
serves the landing page, the lists and the cards.

| Item | Count | Location |
|---|---|---|
| Pages backed by models | 37 | `portal/datasets.py` |
| Prototype pages (no data) | 6 | `about`, `help`, `login`, `register`, `logout`, `admin_index` |
| Total pages | 43 | `portal/pages.py` |

The providers issue real ORM queries: lists use
`select_related`/`prefetch_related` and cap the output (`LIST_LIMIT = 50`
with a truncation flag), cards use `get_object_or_404`, and the quote list
uses the `Max("versions__version")` aggregate to show the latest version
number. Amounts are rendered in Russian format (space as thousands
separator, comma in the fractional part). When the user is not
authenticated, corporate pages show the first enterprise's data and are
flagged with the `demo` mode (access control is stage 5).

The stage document is `docs/Представления_и_данные.docx` (ПЗ, 26 pp.) with
a Chinese counterpart `docs/Представления_и_данные_CN.docx` (26 pp.). The
correspondence tables are generated programmatically: each page provider
is executed against the demo data and the actual database tables are
determined by intercepting SQL queries, so the document cannot drift apart
from the code.

```bash
python tools/check_data.py     # 37 pages with data, 6 prototypes
python manage.py test portal   # 129 tests: models, pages, languages
```

## Interface language

The interface switches between Russian, Chinese and English. The
`RU · 中文 · EN` switcher sits on the right-hand side of the header.

The mechanism is custom, without `gettext`: translations come from the
project data rather than from `.po`/`.mo` files. There is therefore no
second set of translations that could drift apart from the code.

| Layer | Translation source | Volume |
|---|---|---|
| Page titles, purpose, content, route parameters | `portal/pages.py` registry (`ru`/`zh`/`en` fields) | 43 pages |
| Module names M0..M11 | `portal/pages.py` registry | 12 modules |
| Interface texts: navigation, buttons, section headings, footer | `portal/i18n.py`, the `UI` dictionary | 51 keys |
| Data block labels: table and column headings, KPI captions, field keys, empty states | `portal/labels.py`, the `LABELS` dictionary | 385 strings |
| Model enumerations: statuses, document kinds, units of measure, roles, categories, yes/no | `portal/labels.py` (checked against model `choices`) | 108 of 117 |
| Reference values: countries, currencies, units, document types, industries, goods categories | `portal/labels.py` (checked against the reference's `name_zh`) | 12 |
| Administration panel labels: app, model and field names, `help_text`, `choices` labels, panel headings | `portal/admin_labels.py` (checked against the ORM metadata) | 286 |
| Labels the panel keeps in the database: permissions (`Permission.name`) and log messages (`LogEntry.change_message`) | `portal/admin_i18n.py` — rebuilt from the `codename` and from the translated field names | 2 mechanisms |
| Labels inside model `__str__` (“Профиль: …”, “пошлина”, “НДС”, “Диалог: …”, “Перевод #…”) | `portal/labels.py`, through `i18n.label()` | 3 new words |
| Labels of the auto-created M2M relationship models (“Связь dialog-user”), shown on the delete confirmation page | `portal/admin_labels.py`, through `admin_i18n.tr_through_label()` | 2 words × 4 models |

The language is chosen by `portal.middleware.LanguageMiddleware`: the
`?lang=` parameter is stored in the session, so subsequent navigation keeps
the chosen language.

**What is translated and what is not.** The boundary is not “label versus
cell” but “is the string in the dictionary”:

* labels, **model enumerations** (field `choices`) and **reference values**
  are translated — they are interface, even though they arrive as cell
  values;
* **free-form data is not translated**: company and product names, document
  numbers, addresses, dates, amounts, free-text notes. They are absent from
  the dictionary, so `i18n.tr_value()` returns them unchanged — replacing
  data with dictionary entries would falsify the content.

The rule used to be coarser (“never translate cells”), which let Russian
statuses and document types slip past the dictionary. Two composite cases
are also recognised: “Заказ #1” (label plus number) and values joined by a
separator (“Недовоз · Повреждение”, “RU — Россия”).

```bash
/?lang=zh              # Chinese interface
/orders/?lang=en       # English on the order list page
```

The same choice also applies to the administration panel at `/admin/`: its
header carries the `RU · 中文 · EN` switcher (on the login page it sits next
to the title), and Django's own panel strings (buttons, pagination, themes)
come from Django's built-in translations. The switcher links point to a
dedicated route:

```bash
/lang/zh/?next=%2Fadmin%2F   # Chinese panel, returning to /admin/
```

A dedicated route is required because Django treats the `?lang=` parameter
in the panel's list views as an unknown filter and answers with a spurious
redirect (`/admin/portal/order/?lang=zh` → `302` to `?e=1`). The
`portal:set_language` route keeps the return address in `next`, accepts
own paths only (open-redirect protection) and remains compatible with the
`?lang=` parameter in application URLs. Logging out also preserves the
chosen language: `auth_logout()` flushes the whole session, so the logout
view restores the choice.

**Panel labels come from the ORM metadata**, not from the page providers:
the panel reads model and field names from the models themselves
(`verbose_name`, `help_text`, `choices` labels). Django's built-in
translations do not cover them, so the panel shell stayed Russian even with
Chinese selected. The labels are wrapped in a lazy translation
(`portal/admin_i18n.py`): the string is translated when it is rendered, once
the language is known.

| Wrapper | Wraps | Why |
|---|---|---|
| `LazyRu` | `verbose_name`, `help_text`, panel headings | not a `str` subclass: `django.utils.text.capfirst()` tests `isinstance(x, str)` and a subclass would return the Russian text unchanged |
| `LazyChoice` | `choices` labels | a `str` subclass, because `portal/datasets.py` joins them and migrations serialize them; only `str()` is translated |

The wrappers are applied by `PortalConfig.ready()` walking the models, so
new models and fields are translated automatically. Migrations do not
change: `makemigrations` compares `Options.original_attrs`, not the wrapped
values. Labels are looked up first in `ADMIN_LABELS`, then — case
insensitively — in `LABELS`: model labels are lower-case (`валюта`) while
page labels are capitalised (`Валюта`), and the shared dictionary gives them
one translation. Deliberate divergences (`создан` → “创建人”, whereas on the
pages `Создан` is the state “已创建”) are listed explicitly in
`admin_labels.OVERRIDES`.

Free-form data is still shown as-is — including JSON field keys: the panel
is an editing form, and a translated key would be written back to the
database instead of the original. The language names in the switcher
(`title="Русский"`) are also intentional: each language is labelled in
itself.

**Two labels the panel keeps not in metadata but in the database**, and
they are frozen in Russian as well:

* `Permission.name` — at `migrate` it is written as “Can add
  <verbose_name_raw>”, i.e. the Russian model name forever (Django takes the
  untranslated name deliberately so that data does not depend on the
  locale). In the panel this is the permission list on the user and group
  pages: “Can add вложение”. The label is rebuilt from the `codename` — the
  verb comes from Django's own catalogue (the same word as the panel's
  links: Добавить / 增加 / Add), and the model name from its
  `verbose_name`.
* `LogEntry.change_message` — JSON with the names of the changed fields,
  recorded at edit time. Django translates the message as a whole, but there
  are no Russian field names in the catalogue, so the Chinese panel rendered
  “已修改статус 和 дата подписания”. The names are substituted before
  formatting, and the database record itself is not modified.

Finally, the labels inside model `__str__` (“Профиль: …”, “пошлина”,
“НДС”, “Диалог: …”, “Перевод #…”) are hard-coded, yet the panel shows the
object in lists, breadcrumbs and drop-downs — that is, outside
`translate_blocks`. Such words are therefore taken from the dictionary
through `i18n.label()`; the `Profile` label matches the model name
(“Пользователь” / “用户”), the way this entity is named in the stage 1
documents.

**A separate case is the auto-created M2M relationship models**
(`Dialog.participants`, `User.groups` and others). Django builds their
label from a translatable string “%(from)s-%(to)s relationship” and
substitutes the model and field names right away, while importing
`models.py`, with the default locale active — so it becomes an ordinary
Russian string, “Связь dialog-user”, which the lazy translation no longer
picks up. On top of that, such a model has no `__str__` of its own, so the
panel displayed the service form “Dialog_participants object (1)”. Both are
visible on the delete confirmation page, where Django lists the related
objects. `get_models()` (it does not return auto-created models —
`include_auto_created` is off by default) is therefore walked separately:
only the first word of the label is translated, while “dialog-user” stays,
being a technical name identical in every language; and a readable
`__str__` is set, like “Диалог: ORD-2026-0001 — ivanov”.

Page titles and block labels come from the same source as the stage 1–4
documents, so the interface and the explanatory notes cannot diverge.
Dictionary completeness is verified automatically: the providers are
executed against the demo data, while enumerations, reference values and
panel labels are collected by walking the model metadata — every such string
must have a translation.

```bash
python tools/check_lang.py   # 385 labels + 108 enums + 12 reference values + 286 panel labels + 8 M2M relationship labels
```

The Chinese version of the page descriptions contains no Cyrillic (apart
from the conventional designation ИНН) and the Russian version contains no
CJK characters; this is enforced by tests. The legacy `purpose`/`content`
keys in the page registry (aliases of the Chinese variants) are no longer
read by the template directly — the view substitutes the translation for
the current language, so a Russian heading is no longer followed by
Chinese text.

Panel pages are checked the same way — whole rendered HTML, including
lists, forms, history and the user pages with groups. Cyrillic is allowed
only in free-form data (its words are collected from the demo database
across all applications, including the truncations of long text), in the
switcher's language names (`title="Русский"`), and is ignored entirely
inside markup and style comments, which the user never sees.

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
python tools/check_i18n.py      # page registry translation completeness
python tools/check_data.py      # pages wired to models
python tools/check_lang.py      # interface translation completeness
python tools/smoke_test.py      # smoke test: request every page
python tools/gen_docs.py        # refresh docs/pages.{ru,zh,en}.md
python manage.py test portal    # 129 tests: models, pages, languages
```

## Python 3.14 compatibility

`requirements.txt` pins Django 4.2.30 — the branch that supports Python
3.8–3.12 (3.13 arrived in Django 5.1, 3.14 in 5.2). The project is
nevertheless run on newer versions too: the `.venv` virtual environment is
built on Python 3.14.

That is where template context copying breaks. Django 4.2 does this
(`django/template/context.py`):

```python
def __copy__(self):
    duplicate = copy(super())
    duplicate.dicts = self.dicts[:]
    return duplicate
```

The trick relies on attribute access on the `super()` object being
delegated to the wrapped instance, so `copy(super())` returns a copy of the
**context**, not of `super` itself. In Python 3.14 that behaviour changed,
and the second line fails:

```
AttributeError: 'super' object has no attribute 'dicts'
and no __dict__ for setting new attributes
```

Externally it looks misleading: the panel's home page opens (it does not
copy the context), while **every navigation** — to a model list, to a detail
page, to a user — responds with error 500. In the test suite 40 of 120 tests
failed — all of those that render a template with context copying.

The workaround is `portal/compat.py`:

1. **checked by fact, not by version number** — an empty context is copied;
   if the copy succeeds, nothing is touched;
2. **substitution only when broken** — `BaseContext.__copy__` is replaced
   with an implementation without `super()`, repeating the original
   semantics (new object, same `__dict__`, a separate `dicts` list);
3. **idempotent** — the `_portal_compat` marker prevents a second
   substitution;
4. enabled in `PortalConfig.ready()`, next to the panel label translation.

`site-packages` is not modified, no dependency is added, and
`requirements.txt` still pins `Django==4.2.30`. On Python 3.12 and 3.13 the
shim does not engage at all — Django's behaviour stays as shipped. It is
covered by `portal/tests_compat.py`.

## Domain boundaries

The platform takes the position of a “trade collaboration layer” and
deliberately does not perform:

1. payment operations — only recording payment state and party confirmations;
2. customs clearance and certification — only collection, checks and reminders;
3. issuing a final compliance judgement — only facts and a list of missing
   documents;
4. collecting personal data unrelated to business necessity.
