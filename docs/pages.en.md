# Application page list

Course project for the discipline “Web application development in Python”.

Application: “Lightweight collaboration platform for Russia–China cross-border trade” — web client.

> Generated automatically from `portal/pages.py` by `python tools/gen_docs.py`. Do not edit by hand.

## Summary

| Metric | Value |
|---|---|
| Total pages | 43 |
| Modules | 12 |
| Pages with their own Django route | 42 |
| Pages served by `django.contrib.admin` | 1 |

## Routes by module

### M0. Common pages

| No. | Page | Address (URL) | Route name | View | Access |
|---|---|---|---|---|---|
| 1 | Home | `/` | `index` | `index_view` | Public |
| 2 | About the platform | `/about/` | `about` | `about_view` | Public |
| 3 | Help and user guide | `/help/` | `help` | `help_view` | Public |
| 4 | Sign in | `/accounts/login/` | `login` | `login_view` | Public |
| 5 | Sign up | `/accounts/register/` | `register` | `register_view` | Public |
| 6 | Sign out | `/accounts/logout/` | `logout` | `logout_view` | Sign-in required |

### M1. Enterprise and account

| No. | Page | Address (URL) | Route name | View | Access |
|---|---|---|---|---|---|
| 1 | Company bilingual profile | `/enterprises/profile/` | `enterprise_profile` | `enterprise_profile_view` | Sign-in required |
| 2 | Entity verification | `/enterprises/verification/` | `enterprise_verification` | `enterprise_verification_view` | Sign-in required |
| 3 | Members and roles | `/enterprises/members/` | `enterprise_members` | `enterprise_members_view` | Role-restricted |
| 4 | Partner invitations | `/enterprises/invitations/` | `enterprise_invitations` | `enterprise_invitations_view` | Sign-in required |

### M2. Goods

| No. | Page | Address (URL) | Route name | View | Access |
|---|---|---|---|---|---|
| 1 | Goods list | `/goods/` | `goods_list` | `goods_list_view` | Sign-in required |
| 2 | Goods detail | `/goods/<int:pk>/` | `goods_detail` | `goods_detail_view` | Sign-in required |
| 3 | Create or edit goods | `/goods/new/` | `goods_form` | `goods_form_view` | Sign-in required |

### M3. RFQs and quotes

| No. | Page | Address (URL) | Route name | View | Access |
|---|---|---|---|---|---|
| 1 | RFQ list | `/rfqs/` | `rfq_list` | `rfq_list_view` | Sign-in required |
| 2 | Create an RFQ | `/rfqs/new/` | `rfq_create` | `rfq_create_view` | Sign-in required |
| 3 | RFQ detail | `/rfqs/<int:pk>/` | `rfq_detail` | `rfq_detail_view` | Sign-in required |
| 4 | Quotation list | `/quotes/` | `quote_list` | `quote_list_view` | Sign-in required |
| 5 | Quotation detail | `/quotes/<int:pk>/` | `quote_detail` | `quote_detail_view` | Sign-in required |

### M4. Orders

| No. | Page | Address (URL) | Route name | View | Access |
|---|---|---|---|---|---|
| 1 | Order list | `/orders/` | `order_list` | `order_list_view` | Sign-in required |
| 2 | Order detail | `/orders/<int:pk>/` | `order_detail` | `order_detail_view` | Sign-in required |
| 3 | Order milestones | `/orders/<int:pk>/milestones/` | `order_milestones` | `order_milestones_view` | Sign-in required |
| 4 | Order change notes | `/orders/<int:pk>/changes/` | `order_changes` | `order_changes_view` | Sign-in required |

### M5. Logistics and border crossings

| No. | Page | Address (URL) | Route name | View | Access |
|---|---|---|---|---|---|
| 1 | Shipments | `/shipments/` | `shipment_list` | `shipment_list_view` | Sign-in required |
| 2 | Shipment detail | `/shipments/<int:pk>/` | `shipment_detail` | `shipment_detail_view` | Sign-in required |
| 3 | In-transit incidents | `/exceptions/` | `exception_list` | `exception_list_view` | Sign-in required |
| 4 | Report an incident | `/exceptions/new/` | `exception_create` | `exception_create_view` | Sign-in required |

### M6. Documents and compliance

| No. | Page | Address (URL) | Route name | View | Access |
|---|---|---|---|---|---|
| 1 | Document register | `/documents/` | `documents_list` | `documents_list_view` | Sign-in required |
| 2 | Upload documents | `/documents/upload/` | `documents_upload` | `documents_upload_view` | Sign-in required |
| 3 | Certificate validity | `/certificates/` | `certificates_list` | `certificates_list_view` | Sign-in required |
| 4 | Compliance self-check | `/compliance/self-check/` | `compliance_check` | `compliance_check_view` | Sign-in required |

### M7. Bilingual communication

| No. | Page | Address (URL) | Route name | View | Access |
|---|---|---|---|---|---|
| 1 | Conversations | `/messages/` | `message_list` | `message_list_view` | Sign-in required |
| 2 | Conversation detail | `/messages/<int:pk>/` | `message_detail` | `message_detail_view` | Sign-in required |

### M8. Tasks and reminders

| No. | Page | Address (URL) | Route name | View | Access |
|---|---|---|---|---|---|
| 1 | Task board | `/tasks/` | `task_board` | `task_board_view` | Sign-in required |
| 2 | Task detail | `/tasks/<int:pk>/` | `task_detail` | `task_detail_view` | Sign-in required |
| 3 | Notification settings | `/notifications/settings/` | `notification_settings` | `notification_settings_view` | Sign-in required |

### M9. Analytics

| No. | Page | Address (URL) | Route name | View | Access |
|---|---|---|---|---|---|
| 1 | Fulfilment dashboard | `/dashboard/` | `dashboard` | `dashboard_view` | Sign-in required |
| 2 | Lead time and cost | `/dashboard/logistics/` | `dashboard_logistics` | `dashboard_logistics_view` | Sign-in required |
| 3 | Compliance risk dashboard | `/dashboard/compliance/` | `dashboard_compliance` | `dashboard_compliance_view` | Sign-in required |

### M10. Settlements and reconciliation

| No. | Page | Address (URL) | Route name | View | Access |
|---|---|---|---|---|---|
| 1 | Statements | `/statements/` | `statement_list` | `statement_list_view` | Sign-in required |
| 2 | Reconciliation detail | `/statements/<int:pk>/` | `statement_detail` | `statement_detail_view` | Sign-in required |

### M11. Administration

| No. | Page | Address (URL) | Route name | View | Access |
|---|---|---|---|---|---|
| 1 | Audit log | `/system/audit-logs/` | `audit_log_list` | `audit_log_list_view` | Role-restricted |
| 2 | Reference data | `/system/dictionaries/` | `dictionary_list` | `dictionary_list_view` | Role-restricted |
| 3 | Django admin site | `/admin/` | `admin_index` | — (django.contrib.admin) | Role-restricted |

## Page descriptions

### M0. Common pages

#### `/` — Home

- **Route name:** `index`
- **View:** `portal.views.index_view`
- **Access:** Public
- **Purpose:** Presents the platform's positioning, core capabilities and a summary of current to-dos to both anonymous visitors and signed-in users.
- **Main content:** A one-line positioning statement, four capability cards, key figures on China–Russia trade and sign-in/sign-up entry points; when signed in, three extra summary cards for today's tasks, problematic orders and expiring certificates.

#### `/about/` — About the platform

- **Route name:** `about`
- **View:** `portal.views.about_view`
- **Access:** Public
- **Purpose:** Explains the platform's position in the value chain, its four business boundaries and the audiences it serves.
- **Main content:** Platform positioning (trade collaboration layer), the four things it deliberately does not do (payment operations, customs brokerage, deciding compliance outcomes, collecting unrelated personal data) and the three audiences it serves.

#### `/help/` — Help and user guide

- **Route name:** `help`
- **View:** `portal.views.help_view`
- **Access:** Public
- **Purpose:** Provides role-specific operating instructions and answers to frequently asked questions.
- **Main content:** Step-by-step instructions grouped by role (Chinese trader, Chinese sales representative, Russian partner, freight-forwarder operator), a glossary and a FAQ.

#### `/accounts/login/` — Sign in

- **Route name:** `login`
- **View:** `portal.views.login_view`
- **Access:** Public
- **Purpose:** Verifies the user's identity and establishes a signed-in session.
- **Main content:** Account and password fields, "keep me signed in", a switch to one-time-code sign-in and a password-reset link; failed attempts show a clear reason and the number of attempts left.

#### `/accounts/register/` — Sign up

- **Route name:** `register`
- **View:** `portal.views.register_view`
- **Access:** Public
- **Purpose:** Creates a personal account and links it to the company it belongs to.
- **Main content:** Sign-up by phone number or e-mail (supporting China's +86 and Russia's +7 country codes), password-strength validation, a verification-code countdown and a link for attaching a company entity.

#### `/accounts/logout/` — Sign out

- **Route name:** `logout`
- **View:** `portal.views.logout_view`
- **Access:** Sign-in required
- **Purpose:** Ends the current session and clears the local sign-in state.
- **Main content:** A confirmation prompt; after signing out the user is redirected to the home page.

### M1. Enterprise and account

#### `/enterprises/profile/` — Company bilingual profile

- **Route name:** `enterprise_profile`
- **View:** `portal.views.enterprise_profile_view`
- **Access:** Sign-in required
- **Purpose:** Maintains the bilingual profile of the company entity, which serves as the data source for auto-filling documents and contracts.
- **Main content:** Company name, unified social credit code / INN, registered address, contact details and bank information; Chinese and Russian fields are filled in side by side and missing items are highlighted for completion.

#### `/enterprises/verification/` — Entity verification

- **Route name:** `enterprise_verification`
- **View:** `portal.views.enterprise_verification_view`
- **Access:** Sign-in required
- **Purpose:** Submits and tracks company verification documents and governs what unverified entities are allowed to do.
- **Main content:** Upload of a business licence or Russian registration document, confirmation of the extracted fields, review-status tracking (not submitted / under review / approved / rejected) and display of the rejection reason.

#### `/enterprises/members/` — Members and roles

- **Route name:** `enterprise_members`
- **View:** `portal.views.enterprise_members_view`
- **Access:** Role-restricted
- **Purpose:** Manages the company structure, member accounts and role assignments.
- **Main content:** Member list (name, role, status, last sign-in), role assignment, account deactivation and handover; visible only to the business owner and administrators.

#### `/enterprises/invitations/` — Partner invitations

- **Route name:** `enterprise_invitations`
- **View:** `portal.views.enterprise_invitations_view`
- **Access:** Sign-in required
- **Purpose:** Invites Russian partners or freight-forwarder operators to join the collaboration scope of selected orders.
- **Main content:** Choice of invitee type, collaboration scope (by order or by shipment), validity period, invitation link and QR code, and invitation-status tracking.

### M2. Goods

#### `/goods/` — Goods list

- **Route name:** `goods_list`
- **View:** `portal.views.goods_list_view`
- **Access:** Sign-in required
- **Purpose:** Searches the company's goods records by category, status and keyword.
- **Main content:** Card-based list (image, bilingual title, specification summary, compliance flags), frequently used filter tags, sorting and bulk-action entry points.

#### `/goods/<int:pk>/` — Goods detail

- **Route name:** `goods_detail`
- **View:** `portal.views.goods_detail_view`
- **Access:** Sign-in required
- **Route parameters:** pk — goods identifier
- **Purpose:** Shows the complete goods record, its compliance attributes and its version history.
- **Main content:** Bilingual title and description, specification parameters, packaging information, image gallery, HS code and compliance attributes, linked certificates, version history and difference comparison.

#### `/goods/new/` — Create or edit goods

- **Route name:** `goods_form`
- **View:** `portal.views.goods_form_view`
- **Access:** Sign-in required
- **Purpose:** Creates or edits a goods record with bilingual fields.
- **Main content:** Four steps — basic information, specifications, packaging and compliance attributes — with no more than five fields each; a progress indicator at the top; drafts are saved automatically.

### M3. RFQs and quotes

#### `/rfqs/` — RFQ list

- **Route name:** `rfq_list`
- **View:** `portal.views.rfq_list_view`
- **Access:** Sign-in required
- **Purpose:** Shows in one place the requests for quotation the company has sent and received, with their response status.
- **Main content:** Grouped into "started by me / awaiting my response / closed"; each row shows the goods, quantity, target price range, expected delivery date and remaining response time.

#### `/rfqs/new/` — Create an RFQ

- **Route name:** `rfq_create`
- **View:** `portal.views.rfq_create_view`
- **Access:** Sign-in required
- **Purpose:** Lets a Russian partner raise a request for quotation stating quantity, target price and delivery date.
- **Main content:** Goods selection, quantity, target price range, expected delivery date, place of delivery and free-text notes; fits on a single screen and notifies the Chinese side immediately on submission.

#### `/rfqs/<int:pk>/` — RFQ detail

- **Route name:** `rfq_detail`
- **View:** `portal.views.rfq_detail_view`
- **Access:** Sign-in required
- **Route parameters:** pk — RFQ identifier
- **Purpose:** Shows all terms of the request together with linked quotations and allows a direct response.
- **Main content:** RFQ terms, requester and timestamp, list of linked quotations, status-transition log, and entry points for responding and for opening a conversation.

#### `/quotes/` — Quotation list

- **Route name:** `quote_list`
- **View:** `portal.views.quote_list_view`
- **Access:** Sign-in required
- **Purpose:** Shows the quotations the company has issued and received, with their versions and validity periods.
- **Main content:** Each row shows the goods, unit price and currency, trade term, days left before expiry and version number; quotations nearing expiry are highlighted.

#### `/quotes/<int:pk>/` — Quotation detail

- **Route name:** `quote_detail`
- **View:** `portal.views.quote_detail_view`
- **Access:** Sign-in required
- **Route parameters:** pk — quotation identifier
- **Purpose:** Shows all quotation terms, tiered pricing and version history, and allows conversion into an order.
- **Main content:** Unit price, currency, tiered pricing, delivery date, trade term, validity period and notes; version history with difference comparison; once issued a quotation cannot be edited directly — changes create a new version.

### M4. Orders

#### `/orders/` — Order list

- **Route name:** `order_list`
- **View:** `portal.views.order_list_view`
- **Access:** Sign-in required
- **Purpose:** Searches orders by status, corridor and date so that problematic and overdue orders can be found quickly.
- **Main content:** Card-based list (order number, counterparty, current status tag, key dates, next action), status filters, problematic orders pinned to the top and an export entry point.

#### `/orders/<int:pk>/` — Order detail

- **Route name:** `order_detail`
- **View:** `portal.views.order_detail_view`
- **Access:** Sign-in required
- **Route parameters:** pk — order identifier
- **Purpose:** Answers "where is this order now and what happens next" through a three-part layout: status block, milestone timeline and action block.
- **Main content:** Status block at the top (current status, next action, responsible party); milestone timeline in the middle (node, time, operator, evidence thumbnails); action block at the bottom offering only the actions permitted by the user's role and the order's status.

#### `/orders/<int:pk>/milestones/` — Order milestones

- **Route name:** `order_milestones`
- **View:** `portal.views.order_milestones_view`
- **Access:** Sign-in required
- **Route parameters:** pk — order identifier
- **Purpose:** Records and reviews fulfilment milestones in chronological order, forming a traceable chain of evidence.
- **Main content:** Milestone entry form (node type, time, operator, description, evidence upload), a full timeline view, and viewing and downloading of evidence.

#### `/orders/<int:pk>/changes/` — Order change notes

- **Route name:** `order_changes`
- **View:** `portal.views.order_changes_view`
- **Access:** Sign-in required
- **Route parameters:** pk — order identifier
- **Purpose:** Records adjustments to quantity, price, delivery date and delivery details as change notes while keeping the original values.
- **Main content:** Selection of the item to change, before/after comparison, reason for the change and the confirmation status of both parties; until it is confirmed the original terms remain in force.

### M5. Logistics and border crossings

#### `/shipments/` — Shipments

- **Route name:** `shipment_list`
- **View:** `portal.views.shipment_list_view`
- **Access:** Sign-in required
- **Purpose:** Tracks the transport status of each shipment and the corridor it belongs to.
- **Main content:** Shipment list (shipment number, transport mode, corridor, border crossing, current node, estimated arrival); filterable by corridor and border crossing.

#### `/shipments/<int:pk>/` — Shipment detail

- **Route name:** `shipment_detail`
- **View:** `portal.views.shipment_detail_view`
- **Access:** Sign-in required
- **Route parameters:** pk — shipment identifier
- **Purpose:** Records each transport node from pickup to delivery and uploads the supporting evidence.
- **Main content:** Transport mode and waybill number, container and seal numbers (with barcode scanning), the node entry form, lead-time deviation warnings and the evidence list.

#### `/exceptions/` — In-transit incidents

- **Route name:** `exception_list`
- **View:** `portal.views.exception_list_view`
- **Access:** Sign-in required
- **Purpose:** Shows in-transit incidents and how they are being handled.
- **Main content:** Incident list (category, node where it occurred, reporter, report time, handling status); unresolved incidents are pinned to the top and highlighted.

#### `/exceptions/new/` — Report an incident

- **Route name:** `exception_create`
- **View:** `portal.views.exception_create_view`
- **Access:** Sign-in required
- **Purpose:** Lets staff report an incident on site in three steps, automatically attaching time and location.
- **Main content:** Incident category, description, photo upload (compressed automatically with time and location recorded) and links to the order and shipment; can be submitted offline and syncs automatically once the network returns.

### M6. Documents and compliance

#### `/documents/` — Document register

- **Route name:** `documents_list`
- **View:** `portal.views.documents_list_view`
- **Access:** Sign-in required
- **Purpose:** Shows the documents an order requires, by transport mode and goods category, and whether they are complete.
- **Main content:** Checklist items (document type, required or not, uploaded or not, current valid version, uploader, upload time); missing items are highlighted with a shortcut for supplying them.

#### `/documents/upload/` — Upload documents

- **Route name:** `documents_upload`
- **View:** `portal.views.documents_upload_view`
- **Access:** Sign-in required
- **Purpose:** Uploads documents by camera, gallery or file and keeps every version.
- **Main content:** Choice of upload method, document type, file-type and size validation, upload progress with resumable transfers, and version labelling (only one version is valid at a time).

#### `/certificates/` — Certificate validity

- **Route name:** `certificates_list`
- **View:** `portal.views.certificates_list_view`
- **Access:** Sign-in required
- **Purpose:** Records certificate details and gives graded expiry warnings at 60, 30 and 7 days.
- **Main content:** Certificate list (number, issuer, effective date, expiry date, days remaining, linked goods and orders); near-expiry and expired certificates are colour-coded, and certificates tied to open orders are highlighted.

#### `/compliance/self-check/` — Compliance self-check

- **Route name:** `compliance_check`
- **View:** `portal.views.compliance_check_view`
- **Access:** Sign-in required
- **Purpose:** Provides a checklist for item-by-item self-checking that leaves an audit trail and serves as the pre-shipment check.
- **Main content:** A checklist generated from the transport mode, item-by-item ticking, a reason field for failed items and a recorded result on submission; the platform only prompts, it never rules on compliance.

### M7. Bilingual communication

#### `/messages/` — Conversations

- **Route name:** `message_list`
- **View:** `portal.views.message_list_view`
- **Access:** Sign-in required
- **Purpose:** Groups conversations by business object so that discussion never loses its business context.
- **Main content:** Conversation list (linked order / shipment / document / statement, counterparty, last-message preview, unread count); unread conversations are pinned to the top.

#### `/messages/<int:pk>/` — Conversation detail

- **Route name:** `message_detail`
- **View:** `portal.views.message_detail_view`
- **Access:** Sign-in required
- **Route parameters:** pk — conversation identifier
- **Purpose:** Carries on bilingual Chinese–Russian communication within the context of a business object and keeps a record of it.
- **Main content:** Message stream, structured message templates, translation assistance (labelled "machine-assisted translation" and requiring the sender's confirmation), glossary hints, file and image messages, and export of the conversation history per business object.

### M8. Tasks and reminders

#### `/tasks/` — Task board

- **Route name:** `task_board`
- **View:** `portal.views.task_board_view`
- **Access:** Sign-in required
- **Purpose:** Presents tasks grouped as "assigned to me / started by me / overdue" and supports filtering.
- **Main content:** Three board columns, task cards (title, linked business object, owner, time remaining), overdue items pinned and highlighted, plus filtering and bulk actions.

#### `/tasks/<int:pk>/` — Task detail

- **Route name:** `task_detail`
- **View:** `portal.views.task_detail_view`
- **Access:** Sign-in required
- **Route parameters:** pk — task identifier
- **Purpose:** Shows the task details, its handling history and its escalation path.
- **Main content:** Task description, linked business object, owner, response deadline, handling history, acceptance and reassignment, and the record of escalations caused by missed deadlines.

#### `/notifications/settings/` — Notification settings

- **Route name:** `notification_settings`
- **View:** `portal.views.notification_settings_view`
- **Access:** Sign-in required
- **Purpose:** Configures the delivery channel, priority and quiet hours for each type of event.
- **Main content:** Event types and their on/off switches, delivery channels (in-app / SMS / e-mail), quiet hours (applied in each user's own local time), and entry points for switching language and time zone.

### M9. Analytics

#### `/dashboard/` — Fulfilment dashboard

- **Route name:** `dashboard`
- **View:** `portal.views.dashboard_view`
- **Access:** Sign-in required
- **Purpose:** Presents the overall state of fulfilment through summary cards and compact charts.
- **Main content:** Number of orders in progress, status distribution, average fulfilment cycle and a list of overdue orders; three summary cards for today's tasks, problematic orders and expiring certificates, where each figure is itself a link.

#### `/dashboard/logistics/` — Lead time and cost

- **Route name:** `dashboard_logistics`
- **View:** `portal.views.dashboard_logistics_view`
- **Access:** Sign-in required
- **Purpose:** Breaks down average lead times and cost structure by corridor, border crossing and category.
- **Main content:** Corridor lead-time comparison, average customs clearance time per border crossing and cost structure (freight, customs fees, warehousing, transloading); filterable by date range and exportable.

#### `/dashboard/compliance/` — Compliance risk dashboard

- **Route name:** `dashboard_compliance`
- **View:** `portal.views.dashboard_compliance_view`
- **Access:** Sign-in required
- **Purpose:** Brings together expiring and expired certificates, orders with missing documents and outstanding self-checks.
- **Main content:** Risk list ordered by severity (expired certificates, expiring certificates, orders with missing documents, incomplete self-checks), one-click jump to the handling page and export of a risk report.

### M10. Settlements and reconciliation

#### `/statements/` — Statements

- **Route name:** `statement_list`
- **View:** `portal.views.statement_list_view`
- **Access:** Sign-in required
- **Purpose:** Generates statements from the orders and the costs collected against them and tracks their confirmation status.
- **Main content:** Statement list (linked orders, goods value, freight, customs fees, warehousing, total, confirmation status); filterable by date range and counterparty.

#### `/statements/<int:pk>/` — Reconciliation detail

- **Route name:** `statement_detail`
- **View:** `portal.views.statement_detail_view`
- **Access:** Sign-in required
- **Route parameters:** pk — statement identifier
- **Purpose:** Confirms statement lines one by one, flags discrepancies and records how disputes are resolved.
- **Main content:** Line-by-line confirmation, discrepancy flagging with a reason, payment-stage registration (requested / remitted / received, confirmed separately by each party), and an audit trail of disputes with export.

### M11. Administration

#### `/system/audit-logs/` — Audit log

- **Route name:** `audit_log_list`
- **View:** `portal.views.audit_log_list_view`
- **Access:** Role-restricted
- **Purpose:** Queries the record of critical operations such as sign-ins, permission changes, status transitions and data exports.
- **Main content:** Log list (operator, time, object, operation type, before/after values), search by object and time, and export; log entries can be queried but never deleted.

#### `/system/dictionaries/` — Reference data

- **Route name:** `dictionary_list`
- **View:** `portal.views.dictionary_list_view`
- **Access:** Role-restricted
- **Purpose:** Maintains reference data such as border crossings, corridors, trade terms, document types and incident-reason categories.
- **Main content:** Category tree, adding, editing and deleting entries, enabling and disabling them, and maintaining bilingual entries; every change is written to the audit log.

#### `/admin/` — Django admin site

- **Route name:** `admin_index`
- **View:** `django.contrib.admin`
- **Access:** Role-restricted
- **Purpose:** Provides data-maintenance capability through the administration site that ships with the Django framework.
- **Main content:** Model registration, CRUD on data, and user and permission management; supplied by django.contrib.admin and not developed separately.
