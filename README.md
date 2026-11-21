# Order-to-Audit System for a Small Food Manufacturer
**Centre for Digital Infrastructure, NIT Tiruchirappalli — Winter Internship Shortlisting Task**

A complete, production-grade Order-to-Audit prototype connecting field sales orders directly to recipe-based production, immutable ledger-based inventory, costing, and auditor tax reports for a packaged South Indian snacks manufacturer.

> 📺 **Demo Video Walkthrough (Section 5 Benchmark):** [https://youtu.be/-Rm7o3grKjA](https://youtu.be/-Rm7o3grKjA)

---

## 1. Quick Start & Run Commands

You can run the entire system with **a single command**.

### Option A: Local Run (Recommended for fast evaluation)
Requirements: Python 3.11+ / 3.12+ / 3.14+ and Node.js 18+ (pre-built frontend included in `frontend/dist`).

```bash
# 1. Install backend requirements (if not already installed)
pip install -r backend/requirements.txt

# 2. Run the application (starts on http://localhost:8000)
# On Windows:
run.bat
# Or on Linux / macOS:
chmod +x run.sh && ./run.sh
```

Now open:
* **Interactive Web App & Benchmark Runner:** [http://localhost:8000](http://localhost:8000)
* **Interactive Swagger / OpenAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Option B: Docker Compose
```bash
docker compose up --build
```
Open [http://localhost:8000](http://localhost:8000).

---

## 2. Automated Test Suite (100% Section 5 Benchmark Verification)

To programmatically verify all 9 steps of the Section 5 benchmark and all numerical checks:

```bash
# Run the automated pytest suite
pytest -v backend/tests
```

**Output:**
```text
backend/tests/test_api_endpoints.py::test_items_and_purchase_api PASSED
backend/tests/test_api_endpoints.py::test_production_and_dashboard_api PASSED
backend/tests/test_benchmark_section5.py::test_section_5_benchmark_scenario PASSED
============================== 3 passed in 1.1s ==============================
```

---

## 3. Technology Stack & Justification

| Layer | Technology | Justification |
| :--- | :--- | :--- |
| **Backend** | **Python 3.12+ & FastAPI** | Python’s standard library `Decimal` provides IEEE-754 drift-free decimal math for GST, costing, and unit conversions. FastAPI delivers high-performance async APIs, strict Pydantic validation, and instant Swagger docs. |
| **Database** | **SQLite (WAL Mode) / PostgreSQL** | Relational database enforcing foreign key integrity (`PRAGMA foreign_keys=ON`). Configured via SQLAlchemy to seamlessly switch between local SQLite and PostgreSQL. |
| **Inventory Core** | **Immutable Stock Ledger** | Stock balances are derived strictly via `SUM(quantity)` across movements, never overwritten numbers. |
| **Frontend** | **React (Vite) + Tailwind CSS** | Provides role-based responsive views: mobile-card order booking for salesmen (< 1 minute), desktop desk for factory admin, floor tablet view for supervisors, and an executive dashboard. |
| **Document Engine** | **ReportLab & OpenPyXL** | Generates GST-compliant Tax Invoice PDFs and auditor-ready Excel workbooks with formatted stock ledgers. |

---

## 4. Benchmark Scenario Results (Section 5 Verification Table)

All 9 steps of the Section 5 mandatory scenario match with **100% precision**:

| Check Item | Section 5 Expected Check | System Actual Result | Match Status |
| :--- | :--- | :--- | :---: |
| **Flour Closing Balance** | 120 kg $(100 + 60 - 40)$ | **120.00 kg** | ✅ **MATCH** |
| **Cooking Oil Closing Balance** | 19.5 L $(30 - 10.5)$ | **19.50 L** | ✅ **MATCH** |
| **Pouches Closing Balance** | 306 pcs $(500 - 188\text{ used} - 6\text{ damaged})$ | **306 pcs** | ✅ **MATCH** |
| **Finished Goods after Run** | 238 pkts $(50\text{ opening} + 188\text{ produced})$ | **238 pkts** | ✅ **MATCH** |
| **Finished Goods after Retailer A Dispatch** | 88 pkts $(238 - 150)$ | **88 pkts** | ✅ **MATCH** |
| **Yield Variance** | 188 vs 200 expected, -6%, flagged | **-6.00% (FLAGGED)** | ✅ **MATCH** |
| **Oil Consumption Variance** | +5% over standard, flagged | **+5.00% (FLAGGED)** | ✅ **MATCH** |
| **Retailer A GST Invoice** | ₹7,500 taxable + ₹187.50 CGST + ₹187.50 SGST = ₹7,875 | **₹7,875.00** (₹187.50 CGST, ₹187.50 SGST) | ✅ **MATCH** |
| **Retailer A Outstanding** | ₹3,875 $(₹7,875 - ₹4,000\text{ paid})$ | **₹3,875.00** | ✅ **MATCH** |
| **Distributor B Order Shortage** | Shortage of 32 packets flagged; IGST applies if invoiced | **Shortage of 32 pkts flagged; IGST 5% applied** | ✅ **MATCH** |
| **Cost Per Packet** | Stated valuation method & overhead rule | **₹31.14 / pkt** (WAC + ₹1,800 overheads) | ✅ **MATCH** |

### Costing & Valuation Explanation
* **Valuation Method:** Moving Weighted Average Cost (WAC).
  * Flour Opening: 100 kg @ ₹42 = ₹4,200
  * Flour Purchase: 60 kg @ ₹45 = ₹2,700
  * WAC Rate: $\frac{₹4,200 + ₹2,700}{160} = \mathbf{₹43.125/\text{kg}}$
  * 40 kg consumed = **₹1,725.00**
* Direct Materials Total: ₹1,725 (Flour) + ₹1,470 (Oil) + ₹240 (Spice) + ₹485 (194 Pouches) + ₹135 (9 Cartons) = **₹4,055.00**.
* Overheads: Labour (₹1,200) + Power/Gas (₹600) = **₹1,800.00**.
* **Batch Cost:** ₹4,055 + ₹1,800 = **₹5,855.00**.
* **Cost per packet:** $\frac{₹5,855}{188} = \mathbf{₹31.14 / \text{packet}}$ (Gross Margin: **37.72%** against ₹50 selling price).

---

## 5. Scope Matrix (Section 6 Tiers)

### Must-Have Features (All Completed)
* [x] Login & role switching for 5 distinct roles (Salesman, Admin, Production, Auditor, Owner).
* [x] Product, Customer, Raw Material, Packaging, and BOM Master Data.
* [x] Mobile-friendly order entry (< 1 minute order flow) with admin approval.
* [x] GST-compliant Tax Invoice generation as downloadable PDF.
* [x] Recipe-based production run that updates raw, packaging, and finished goods stock atomically.
* [x] Planned vs actual consumption and yield, with automatic variance flagging beyond 3%.
* [x] Always-current stock summary (Opening + Receipts - Issues = Closing) & immutable stock ledger.
* [x] Sales register and stock report exportable to Excel (`.xlsx`).

### Should-Have Features (All Completed)
* [x] Raw material purchases & supplier records (Step 1).
* [x] Payments, receivables outstanding, and customer aging ledger (Step 7).
* [x] Cost per packet calculation with overheads (Labour & Power allocation).
* [x] GSTR-1 / GSTR-3B compliant outward supplies summary with Place of Supply split.
* [x] Variance alert system for deviations exceeding tolerance.
* [x] Executive Owner Dashboard with real-time operational KPIs.

### Stretch Goals Implemented
* [x] **Interactive Benchmark Player:** A built-in UI tool that runs the 9 Section 5 benchmark steps live on screen.
* [x] **Immutable Audit Trail & Credit Notes:** Posted invoices are cancelled with credit note reversal entries, never deleted.
* [x] **Ready for 500g Pack Extension:** Built-in support to add secondary pack sizes sharing the same BOM.

---

## 6. Assumptions & Documented Rules

1. **Place of Supply:** Factory is located in Tamil Nadu (State Code 33). Deliveries within Tamil Nadu incur Intra-state tax (**CGST 2.5% + SGST 2.5%**). Deliveries to other states (e.g., Karnataka, State Code 29) incur Inter-state tax (**IGST 5.0%**).
2. **Damaged Packaging:** The 6 damaged pouches during production are recorded as `SCRAP_DAMAGE` in the stock ledger and included in batch material cost, reflecting real-world manufacturing wastage.
3. **Paisa Precision:** All calculations use integer-paisa or `Decimal(12, 4)` representation. No floating-point values are stored or calculated for currency or inventory.

---

## 7. Project Structure

```
├── backend/
│   ├── app/
│   │   ├── config.py              # Configuration & GST constants
│   │   ├── database.py            # SQLite / PostgreSQL engine with PRAGMA FK
│   │   ├── models/                # SQLAlchemy models (Items, BOM, Ledger, Invoices)
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── services/
│   │   │   ├── ledger_service.py  # Immutable ledger summation & movements
│   │   │   ├── production_service.py # BOM yield, consumption variance & costing
│   │   │   ├── sales_service.py   # Orders, GST calculation & dispatches
│   │   │   └── report_service.py  # GSTR summaries, PDF & Excel export
│   │   ├── routers/               # FastAPI route controllers
│   │   ├── seed.py                # Populates Section 5 master data & opening balances
│   │   └── main.py                # FastAPI app entry point & static file server
│   ├── tests/
│   │   ├── test_benchmark_section5.py # Automated verification of Section 5 checks
│   │   └── test_api_endpoints.py      # End-to-end API router tests
│   └── requirements.txt
├── frontend/                      # React (Vite) + Tailwind CSS UI
│   ├── src/
│   │   ├── views/                 # Salesman, Admin, Production, Auditor, Owner, Benchmark views
│   │   ├── App.tsx
│   │   └── api.ts
│   └── dist/                      # Production build served directly by FastAPI
├── DESIGN_NOTE.md                 # 2-Page architecture & valuation design note
├── Dockerfile                     # Multi-stage production container
├── docker-compose.yml             # Single-command deployment definition
├── run.bat                        # Windows 1-click startup
└── run.sh                         # Linux/macOS 1-click startup
```
