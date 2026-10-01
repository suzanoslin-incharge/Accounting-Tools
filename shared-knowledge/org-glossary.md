# InCharge Org Glossary (shared knowledge)

Seed version, pulled from the Accounting knowledge base on 2026-09-28.
Updated 2026-10-01 with department names and abbreviations from the
InCharge Departments and Key People directory (roster dated 2026-07-20); full directory table added below.
Anyone using a skill that touches process mapping should treat this as a
starting point, not a verified directory — confirm names/roles before
publishing anything outward-facing.

## Lines of business

Four revenue-producing lines of business (LOB). The four-LOB structure and the
"Turn Chargers On / Keep Chargers On" mapping are a working framing for
finance and reporting, not an approved taxonomy; confirm with Finance.

- **Service** — Reactive and planned field-service work delivered against a
  Work Order.
  - Tracked in Salesforce/ServiceMax (SVMX); dispatch driven; technician
    labor and parts usage.
  - Time & Materials or contract billable. Billed once a Work Order reaches
    the Ready-to-Invoice milestone. Responsibility Center = SERVICE.
  - Examples: charger repair, warranty repair, PM inspections, cable
    replacements, troubleshooting visits.
- **EPC** (Engineering, Procurement, Construction) — Project-based delivery
  of charging infrastructure.
  - Identified by project number, which carries a state-code suffix (e.g.
    `395876CA`). Managed in Procore; also tracked in Excel/Smartsheet and
    Business Central (BC).
  - Construction activities, progress billing, change orders, revenue
    recognition by project.
  - Examples: new depot construction, fleet charging installation, utility
    upgrades, site commissioning.
- **Software** — Sale of software products and software renewals.
  - InControl is the standalone software offering in the internal product
    catalog. Software licenses and renewals.
  - Typically invoiced 100% upfront at contract start; moving to
    PayFabric-based payment collection (payment links from Salesforce quotes).
  - Examples: InControl subscriptions, annual renewals, expansion licenses.
- **Recurring Services** (Managed & Recurring Services) — Ongoing
  contractual services that produce recurring revenue independent of
  individual Work Orders.
  - Examples: LASO, DASSO, subscription support programs, managed charging
    services, partnerships such as Voltpost.
  - The area creating the most process strain: it fits neither Service Work
    Orders nor EPC projects, and current tooling doesn't yet support it well.

**Enabling functions** (not revenue-producing LOBs): Sales, Product
Development, Finance, Warehouse / Fulfillment, Asset Management, NOC,
Technical Support, HR, IT.

**Executive summary.** InCharge is in the business of "Turn Chargers On" and
"Keep Chargers On" (SKO deck):

| Theme | LOBs |
|---|---|
| Turn Chargers On | EPC + Software |
| Keep Chargers On | Service + Recurring Services |

EPC and Software get chargers deployed and operational; Service and
Recurring Services keep them operating over time.

## Common abbreviations

- **RSS** — Regional Service Specialist
- **BC** — Business Central (ERP / general ledger)
- **SF** — Salesforce
- **SVMX** — ServiceMax
- **O2C** — Order-to-Cash
- **P2P** — Procure-to-Pay
- **R2R** — Record-to-Report
- **WO** — Work Order
- **SIPOC** — Suppliers, Inputs, Process, Outputs, Customers (see
  `skills/sipoc-builder`)
- **AP** — Accounts Payable
- **AR** — Accounts Receivable
- **PO** — Purchase Order
- **NOC** — Network Operations Center
- **HSE** — Health, Safety & Environment
- **EVCS** — EV charging station (as in "EVCS Technician")
- **EVSE** — Electric vehicle supply equipment (charger assets)
- **OEM** — Original equipment manufacturer (OEM Sales)
- **QA** — Software Quality Assurance
- **UX** — User experience / product design
- **LMS** — Learning management system (Cornerstone LMS, Technical Training)
- **HR** — People / Human Resources

## Departments and functions

Names as they appear in the department directory. Treat the groupings as a
working classification: the directory is a starting point, not an official org
chart, and assignments may have changed since the roster date.

- **Leadership** — Executive Leadership; Finance Executive Leadership; Sales
  Executive Leadership; Service Executive Leadership.
- **Finance** — Finance / Accounting; Accounts Payable; Accounts Receivable /
  Collections; Business Analytics / Finance Analytics.
- **People and legal** — People / HR; Recruiting; Legal; Technical Training;
  Health, Safety & Environment.
- **Sales and customer** — Enterprise / Major Accounts Sales; Regional / Direct
  Sales; OEM Sales; Channel Sales; Service Sales; Sales Operations; Strategic
  Accounts; Customer Experience / Customer Support; Marketing &
  Communications; Government Relations / Public Affairs; Energy Solutions /
  Business Development.
- **Product and technology** — Digital Product; Digital Product Analytics /
  Systems; Software Engineering; Software Quality Assurance; UX / Product
  Design; Hardware / Product Engineering; Technology / IT.
- **Service** — Service Management; Service Account Management; Service
  Assets; Dispatch / Service Coordination; NOC; Technical Support; Payment
  Services; Parts; Field Service Operations (Southeast, Northeast, Southwest,
  Central, Midwest, Northwest); Canada Operations; Branch Operations;
  Efficient / Lighting Operations.
- **EPC and engineering** — EPC Leadership / Administration; EPC / Project
  Management; Project Coordination; Field Construction / Site Supervision;
  Electrical Engineering / Proposals; Electrical Design; Sales Engineering;
  Program Management.
- **Supply chain** — Supply Chain / Supply Management; Purchasing / Inventory;
  Logistics; Warehouse / Production; Warehouse Material Handling.

People, titles, and the systems each team uses are in the directory below.

## Department directory: key people, systems, processes

> Working directory based primarily on the employee roster dated July 20, 2026. This is a starting point, not an official organization chart. Employee assignments may have changed after the roster date.

> **Draft-field note:** Values marked **Proposed** in Systems Used, Common Processes, or Related Teams are working classifications added to make the directory more useful. They should be confirmed by the applicable department.

| Department / Function | Key People and Titles | Systems Used | Common Processes | Related Teams |
|---|---|---|---|---|
| Executive Leadership | Richard Mohr (Chief Executive Officer); Terence O'Day (Chief Operation Officer); Cameron Funk (Chief Electrical & Workforce Development Officer) | Proposed: enterprise reporting; Business Central; ADP | Proposed: corporate strategy; operational oversight; workforce development | Proposed: Finance; HR; Sales; Service; EPC; Product; Technology |
| Finance Executive Leadership | Adrian Foltz (Chief Financial Officer); Carrie Preston (Director of Accounting); CJ Calloway (Financial Accounting Manager) | Business Central; RAMP; ADP | Financial reporting; accounting oversight; expense and payment controls | Executive Leadership; Accounting; AP; AR; Procurement; department budget owners |
| Finance / Accounting | Carrie Preston (Director of Accounting); Shree Harrell (Revenue Accounting Manager); Joshua Barnhill (Manager of Accounts Receivable & Fleet) | Business Central; RAMP | Accounting and reporting; revenue accounting; receivables; financial coding | AP; AR; Sales; Service; EPC; Procurement |
| Accounts Payable | Cynthia Smithson (Accounts Payable Specialist); Carrie Preston (Director of Accounting); CJ Calloway (Financial Accounting Manager) | Business Central; Outlook shared mailbox | Invoice intake; PO-receipt-invoice matching; payment processing; supplier inquiries | Purchasing; Finance; business owners; Warehouse; Service; EPC |
| Accounts Receivable / Collections | Joshua Barnhill (Manager of Accounts Receivable & Fleet); Stunique Crossin (Senior Collections Specialist); Shree Harrell (Revenue Accounting Manager) | Business Central; Proposed: Salesforce | Receivables; collections; revenue accounting; fleet-related accounting | Sales; Finance; Customer Experience; Service |
| Business Analytics / Finance Analytics | Kristine Do-Vu (Business Analytics Manager); Xander Boldt (Business Analyst I); Brian Bondurant (Financial Consultant) | Business Central; Excel; Proposed: Power BI | Business analysis; financial analysis; reporting; department-code and roster analysis | Finance; Executive Leadership; HR; department leaders |
| People / HR | Gina Elia (VP of People); Margaret Brazell (Senior HR Business Partner); Frances Jarrell (Senior HR Systems Analyst) | ADP; Active Directory | HR data management; employee support; workforce administration | Recruiting; Training; HSE; IT; department leaders |
| Recruiting | Angelyca Poole (Recruiting Manager); Lauren Gutzmer (Corporate Recruiter); Eric Sawyer (Recruiting Coordinator) | ADP; Proposed: recruiting systems | Recruiting; candidate coordination; onboarding | HR; hiring managers; department leaders |
| Legal | Azizza Jones (Paralegal); Richard Mohr (Chief Executive Officer); Terence O'Day (Chief Operation Officer) | Proposed: SharePoint; contract repositories | Proposed: legal support; contract coordination; corporate governance | Executive Leadership; Finance; Procurement; Compliance; department leaders |
| Sales Executive Leadership | Dennis Carter (Chief Revenue Officer); Virginia Hewitt (Sr. Director of Enterprise Accounts); Joshua Murray (Director of OEM Sales) | Salesforce; Proposed: Business Central | Sales leadership; enterprise accounts; OEM sales | Sales Operations; Marketing; Product; EPC; Customer Experience; Finance |
| Enterprise / Major Accounts Sales | Virginia Hewitt (Sr. Director of Enterprise Accounts); Michael Heller (Enterprise Account Manager); Anthony Lumino (Senior Account Executive) | Salesforce | Enterprise account development; account management; opportunity coordination | Sales Operations; EPC; Product; Service; Customer Experience |
| Regional / Direct Sales | Micalina Grove Juarez (Inside Sales Manager); Erica Madden (Regional Account Executive); Ryan Gavagan (Account Executive) | Salesforce | Lead and opportunity management; regional sales; customer engagement | Sales Operations; Marketing; Product; EPC |
| OEM Sales | Joshua Murray (Director of OEM Sales); Drew Blake (Account Executive OEM); Kenneth Malone (Account Executive - OEM Fleet) | Salesforce | OEM and fleet account development; opportunity management | Product; Hardware; Service; Sales Operations; EPC |
| Channel Sales | Molly Roth (Director of Channel Sales); Anit Soni (Channel Development Manager); Micalina Grove Juarez (Inside Sales Manager) | Salesforce | Channel development; partner sales; inside sales | Marketing; Product; Sales Operations; Customer Experience |
| Service Sales | Adam Everman (National Service Sales Director); Katie Veerkamp (Manager of Strategic Accounts Service & Support); Michael Scheeper (Head of Customer Experience & Support Operations) | Salesforce; ServiceMax | Service sales; strategic-account support; customer experience coordination | Service Management; NOC; Sales; Customer Experience |
| Sales Operations | Katrina Schurawel (Senior Sales Operations Manager); April Frank (Sales Engagement Analyst); Miaka Golden (Sales Operations Specialist) | Salesforce; Business Central | Customer-data ownership; sales process support; sales engagement; reporting | Sales; Finance; Marketing; Product; EPC |
| Strategic Accounts | Virginia Hewitt (Sr. Director of Enterprise Accounts); Michael Heller (Enterprise Account Manager); Alexander Soulas (Sr Project Manager Strategic Accounts) | Salesforce; Procore; Proposed: Business Central | Strategic-account management; project coordination; customer engagement | Sales; EPC; Service; Customer Experience; Finance |
| Customer Experience / Customer Support | Michael Scheeper (Head of Customer Experience & Support Operations); Kevin Wright (Vice President of Support Operations); Bilal Ahsan (Director of Support Operations) | Salesforce; ServiceMax; Proposed: support channels | Customer support; support-operations leadership; cross-department issue coordination | NOC; Service Management; Sales; Product; Software |
| Marketing & Communications | Justin Wong (Senior Marketing Manager); Laura Karrer (Digital Marketing Specialist); Junko Green (Director of Customer Engagement, Software) | Proposed: website and digital-marketing platforms; Salesforce | Marketing communications; digital marketing; software customer engagement | Sales; Product; Software; Executive Leadership |
| Government Relations / Public Affairs | Laura Rivas (Manager, Grants, Opportunities, and Public Affairs); Kelly Bernd (Senior Proposal and Grant Specialist); Claire Disch (Proposal and Grant Specialist) | Proposed: SharePoint; proposal and grant repositories | Grant and proposal support; public affairs; opportunity tracking | Sales; EPC; Engineering; Finance; Executive Leadership |
| Digital Product | Russell Schmidt (Vice President of Digital Products); Oleksandra Huynh (Senior Product Manager); Jason Haren (Senior Product Manager) | Salesforce; Jira; Proposed: product collaboration tools | Product management; digital-product planning; requirements and roadmap coordination | Software Engineering; UX; Sales; Service; Marketing |
| Digital Product Analytics / Systems | Marina Lukoshko (Manager of Data Analytics); Priya Keshri (Salesforce Administrator); Aaron Connell (Salesforce Engineer) | Salesforce; Proposed: analytics tools | Data analytics; Salesforce administration; Salesforce engineering | Digital Product; Sales Operations; Service; Finance; Software |
| Software Engineering | Siarhei Ahranovich (VP of Software Engineering); Andre Napier (Sr Manager, Product Engineering); Felipe Nogaroto Gonzalez (Senior DevOps Engineer) | Jira; Proposed: software-development and DevOps platforms | Software engineering; product engineering; DevOps | Digital Product; QA; UX; IT; Support |
| Software Quality Assurance | Ihar Strelka (Software Quality Assurance Engineer); Hanna Vysotskaya (Lead Quality Assurance); Brian Ives (Senior QA Engineer) | Jira; Proposed: test-management tools | Software quality assurance; test planning; validation | Software Engineering; Digital Product; Support |
| UX / Product Design | Nicole Gose (Software UX Designer); Isaac Sanmiguel (UX Researcher); Sarai Garcia (Software UX Designer Intern) | Proposed: design and research tools; Jira | UX design; user research; product-design support | Digital Product; Software Engineering; Marketing; Customer Experience |
| Hardware / Product Engineering | Andre Napier (Sr Manager, Product Engineering); Alexander Petze (Product Manager EV Charging); Zoe Nettles (Hardware Documentation Specialist) | Proposed: engineering and documentation repositories | Product engineering; EV charging product management; hardware documentation | Digital Product; Software; Training; Service; Supply Chain |
| Technology / IT | Nikolas Runge (Chief Technology Officer); Jack Ehlers (IT Operations Manager); Alexander Som (IT Operations and Security Analyst) | Active Directory; Proposed: IT service and security platforms | IT operations; security; access and infrastructure support | Software Engineering; HR; all departments |
| Technical Training | Sean Gossard (Director of Technical Training); Ben Nicol (Senior Technical Training Manager); Niko Bardacke (Cornerstone LMS Administrator Intern) | Cornerstone LMS; Proposed: SharePoint | Technical training; learning administration; certification support | Service; Field Operations; Hardware; HSE; HR |
| Service Executive Leadership | Kevin Wright (Vice President of Support Operations); Sierra Wilkins (Director of Service Delivery); Bilal Ahsan (Director of Support Operations) | ServiceMax; Salesforce | Service delivery; support operations; service-process leadership | Service Management; NOC; Field Operations; Parts; Training; Sales |
| Service Management | Sierra Wilkins (Director of Service Delivery); Matt Burnette (Director of Service Estimating); Kylie Schiller (Sr. Dispatch Manager) | ServiceMax; Salesforce; Business Central; RAMP | Service delivery; estimating; dispatch; service PO coordination | Field Operations; NOC; Parts; Accounting; Purchasing; Training |
| Service Account Management | Katie Veerkamp (Manager of Strategic Accounts Service & Support); Amber Blough (Service Account Manager); Ana Maria Stallings (Service Account Manager) | Salesforce; ServiceMax | Service-account management; customer coordination; strategic-account support | Sales; Service Management; NOC; Customer Experience |
| Service Assets | William Bruce (Senior Asset Manager); Robert Loyd (Asset Manager, EVSE); Daisy Calderon (Asset Specialist) | Salesforce; ServiceMax | EVSE asset management; asset-data support | Service Management; NOC; Product; Field Operations |
| Dispatch / Service Coordination | Kylie Schiller (Sr. Dispatch Manager); Dean Ruth (Manager of Project Coordinators); Steven Rivera (Service Manager) | ServiceMax; Salesforce | Dispatch; work-order coordination; service scheduling; case-to-work-order handoffs | Field Operations; Parts; NOC; Service Management |
| NOC / Network Operations Center | James Tuppince (Network Operations Center Manager); Christian Dunston (Technical Support Manager); Michelle Vassallo (Payment Services Manager) | Salesforce; ServiceMax; Proposed: network-monitoring and payment platforms | Network operations; technical support; payment services | Service Management; Software; Product; Customer Experience; Sales |
| Technical Support | Christian Dunston (Technical Support Manager); Shannon Hawkins (Technical Support Specialist II); Katrina Kirby (Technical Support Specialist II) | Salesforce; ServiceMax | Technical support; case handling; troubleshooting coordination | NOC; Service Management; Product; Software; Field Operations |
| Payment Services | Michelle Vassallo (Payment Services Manager); Austin Daniel (Payment Specialist); James Tuppince (Network Operations Center Manager) | Proposed: payment-services platforms; Salesforce | Payment-services support; payment issue coordination | NOC; Customer Experience; Sales; Finance |
| Field Service Operations | Kevin Wright (Vice President of Support Operations); Sierra Wilkins (Director of Service Delivery); Van Wilkins (Executive Vice President of Enterprise Growth) | ServiceMax; Salesforce; RAMP | Regional field service; technician deployment; service delivery | Service Management; Dispatch; Training; Parts; HSE |
| Southeast Field Service | Iqwon McRae (Regional Service Manager); Brian Moats (EVCS Technician Lead); Walter Clark (EVCS Technician) | ServiceMax; RAMP | Regional dispatch execution; EVCS field service; work-order completion | Service Management; Dispatch; Parts; NOC; Training |
| Northeast Field Service | Richard Morris (EVCS Technician Lead); Lance Carmack (EVCS Technician); David Santos (EVCS Technician) | ServiceMax; RAMP | EVCS field service; work-order completion | Service Management; Dispatch; Parts; NOC; Training |
| Southwest Field Service | Connor Clabaugh (Associate Regional Service Manager); David Leal (EVCS Technician); Martha Rivera Perez (EVCS Technician) | ServiceMax; RAMP | Regional service management; EVCS field service; work-order completion | Service Management; Dispatch; Parts; NOC; Training |
| Central Field Service | Alicia Tafolla (General Manager); Chukwu Ideghe (EVCS Technician); Kevin Lamson (EVCS Technician) | ServiceMax; RAMP | Regional operations; EVCS field service; work-order completion | Service Management; Dispatch; Parts; NOC; Training |
| Midwest Field Service | James McNiece (Regional Service Manager); Lillique Leasure-Burnett (EVCS Technician); Amos Jones (EVCS Technician) | ServiceMax; RAMP | Regional service management; EVCS field service; work-order completion | Service Management; Dispatch; Parts; NOC; Training |
| Northwest Field Service | Frank Dolence (Regional Service Manager); William Ervin (EVCS Technician) | ServiceMax; RAMP | Regional service management; EVCS field service; work-order completion | Service Management; Dispatch; Parts; NOC; Training |
| Canada Operations | Ian Houghton (EVCS Technician); Shahram Farzinpak (EVCS Technician); Hanna Vysotskaya (Lead Quality Assurance, R&D Canada) | ServiceMax; Proposed: software QA tools | EVCS field service in Canada; software quality assurance in Canada | Service Management; Software QA; Dispatch; Product |
| EPC Leadership / Administration | Cordes Towles (Senior Director of Project Management); Ericka White (Project Administrator); Clinton Smith (Senior Electrical Construction Estimator) | Procore; Business Central; Salesforce | EPC administration; project governance; estimating; project-spend controls | Project Management; Engineering; Finance; Procurement; Sales |
| EPC / Project Management | Marcus Kilgo (Director of Project Management); Dragos Ionescu (Senior Project Manager); Mark Womack (Site Superintendent III) | Procore; Business Central; Salesforce | Project management; site execution; subcontractor and project-spend coordination | EPC Administration; Engineering; Finance; Procurement; Warehouse |
| Project Coordination | Dean Ruth (Manager of Project Coordinators); Mireille Veltman (Senior Project Coordinator II); Bianca Velarde (Senior Project Coordinator I) | Procore; Salesforce; Proposed: SharePoint | Project coordination; documentation; schedule and handoff support | Project Management; Engineering; Sales; Finance |
| Field Construction / Site Supervision | Gus Eleopoulos (Field Supervisor Lead); Donald Schmidt (Site Superintendent III); William Sullivan (Site Superintendent) | Procore; RAMP | Site supervision; construction execution; field coordination | Project Management; Engineering; HSE; Procurement |
| Electrical Engineering / Proposals | Joseph Crader (Director of Electrical Engineering); Taylor Minnick (Engineering Operations Manager); James Yi (Electrical Infrastructure Engineer III) | Proposed: engineering design tools; Procore; SharePoint | Electrical engineering; infrastructure design; proposal support | Sales Engineering; EPC; Product; Sales |
| Electrical Design | Edward Kovar (Electrical Design Engineer III); Chang Seo (Electrical Design Engineer I); Galaad Garcon-Tremblay (Electrical Design Drafter) | Proposed: electrical design and drafting tools | Electrical design; drafting; project-design support | Electrical Engineering; EPC; Sales Engineering |
| Sales Engineering | Dominic Lucchesi (Sales Engineer); Joseph Crader (Director of Electrical Engineering); Taylor Minnick (Engineering Operations Manager) | Salesforce; Proposed: engineering design tools | Technical sales support; solution definition; proposal engineering | Sales; Electrical Engineering; EPC; Product |
| Program Management | Gabija Kulichenko (Senior Program Manager); Russell Schmidt (Vice President of Digital Products); Marcus Kilgo (Director of Project Management) | Proposed: Jira; Procore; SharePoint | Program planning; cross-functional coordination; delivery oversight | Digital Product; EPC; Software; Sales |
| Supply Chain / Supply Management | Edgaras Venckus (Director of Supply Chain & Product Coordination); Austin Woisard (Logistics Manager); Gintare Savelskas (Senior Supply Chain & Product Data Analyst) | Business Central; SharePoint | Supply planning; logistics; product data; supplier coordination | Purchasing; Warehouse; Finance; EPC; Service; Product |
| Purchasing / Inventory | Edgaras Venckus (Director of Supply Chain & Product Coordination); Samuel Kesolei (Purchasing & Inventory Specialist); Gintare Savelskas (Senior Supply Chain & Product Data Analyst) | Business Central; TrustLayer; Compass; SharePoint | Purchase orders; supplier governance; inventory support; receipt processing | Warehouse; AP; Finance; EPC; Service; Compliance |
| Logistics | Austin Woisard (Logistics Manager); Matthew Holloman (Logistics Coordinator); Edgaras Venckus (Director of Supply Chain & Product Coordination) | Business Central; SharePoint | Shipping and logistics coordination; material movement; delivery support | Warehouse; Purchasing; EPC; Service; Sales |
| Warehouse / Production | Leeana Nguyen (Quality & Parts Manager); Patrick Arevalo (Electrical & Safety Manager); Ernest Roberts (Production Technician I) | Business Central; JotForm | Inbound receiving; warehouse put-away; bin management; inventory and non-inventory receipt posting | Shipping & Receiving; Logistics; Inventory; Accounting; Purchasing |
| Warehouse Material Handling | Lamont Carpenter (Senior Material Handler); Nathan Shepard (Material Handler); Terrell Eberhardt (Material Handler) | Business Central; JotForm | Material handling; receiving support; put-away; warehouse movement | Warehouse; Logistics; Purchasing; Parts |
| Parts | Leeana Nguyen (Quality & Parts Manager); Aydian Woodard (Parts Coordinator); Samuel Kesolei (Purchasing & Inventory Specialist) | ServiceMax; Salesforce; Business Central | Parts identification; sourcing; ordering; tracking; delivery confirmation before dispatch | Service Management; Dispatch; Warehouse; Purchasing; Accounting |
| Health, Safety & Environment | Lon Bartoli (HSE Manager); Cody Anderson (Contractor Compliance Program Manager); Patrick Arevalo (Electrical & Safety Manager) | TrustLayer; Compass; Drata | Contractor compliance; supplier-risk controls; health and safety support | HR; EPC; Field Operations; Procurement; Warehouse |
| Branch Operations | Michael Gallagher (Head of Branch Operations); De'Ontae Hall (General Manager); Francisco Amigon (Service Manager) | ServiceMax; RAMP; Proposed: branch operations systems | Branch operations; service delivery; technician and field coordination | Service; Sales; HSE; Finance; HR |
| Energy Solutions / Business Development | David Callaghan (Business Development Manager, Energy Solutions); Michael Gallagher (Head of Branch Operations); Michael Fogerty (Manager of Strategic Accounts - Renewable Energy) | Salesforce; Proposed: proposal and project tools | Business development; renewable-energy accounts; opportunity development | Sales; Branch Operations; EPC; Engineering; Marketing |
| Efficient / Lighting Operations | Michael Gallagher (Head of Branch Operations); De'Ontae Hall (General Manager); Francisco Amigon (Service Manager) | ServiceMax; RAMP; Proposed: branch operations systems | Lighting and electrical field operations; service management; branch coordination | Branch Operations; Field Operations; HSE; Sales; Finance |

### Source

- Roster as of 07.20.26.xlsx
- Additional process and system references from the InCharge P2P transformation materials, warehouse metadata standard, and service-parts workflow notes used earlier in this working directory.

## Full detail

For the fuller current-state picture (systems, people, process narratives),
see the Accounting team's working knowledge base:
`Accounting-MyNotes/Current-State Accounting Processes Report.md`. That
folder is a personal/team working notebook, not synced into this repo — pull
a curated summary in here if a skill needs to load it automatically.
