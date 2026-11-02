# Document Intelligence

A plain-English reference for Azure AI Document Intelligence. Written so anyone can read it and learn.

---

## What is Document Intelligence

Every business runs on documents — invoices, contracts, receipts, ID cards, tax forms, bank statements. These are either scanned images or PDFs, and the data inside them is locked away. Someone has to read the document and manually type the values into a system.

**Document Intelligence automates that.** You send a document (PDF, image, or URL), and the service sends back structured JSON with all the fields extracted and labelled.

This is different from plain OCR (like the Read API in Computer Vision). OCR extracts raw text. Document Intelligence extracts *meaning* — it knows that "Invoice #" is the invoice number, "$500.00" is the total, and "Contoso Ltd" is the vendor.

---

## Document Intelligence vs OCR — the difference

| OCR (Computer Vision Read API) | Document Intelligence |
|---|---|
| Extracts raw text | Extracts structured, labelled fields |
| Returns words and positions | Returns `InvoiceId: "12345"`, `VendorName: "Contoso"` |
| No understanding of structure | Understands tables, key-value pairs, form fields |
| Good for: raw text from any image | Good for: business documents with known structure |

Use OCR when you just need the text. Use Document Intelligence when you need the fields.

---

## The Azure Resource

Document Intelligence needs its own dedicated resource. It is **not** covered by the multi-service `CognitiveServices` account.

- **Terraform kind:** `"FormRecognizer"` — this is the real resource kind in Azure, even though the service was renamed to Document Intelligence. Same pattern as Translator using `"TextTranslation"` — the service name changed but the underlying resource kind did not.
- **SKU:** `F0` (free tier — 500 pages/month)
- **SDK package:** `azure-ai-documentintelligence`

---

## The Models

### Pre-built Models

Microsoft has trained models for the most common document types. Use these first — you do not need to collect training data or label anything.

| Model ID | Document type | What it extracts |
|---|---|---|
| `prebuilt-invoice` | Business invoices | Vendor, customer, line items, subtotal, tax, total, dates |
| `prebuilt-receipt` | Retail receipts | Merchant, date, items purchased, total, tip |
| `prebuilt-idDocument` | Passports, driver's licences | Name, date of birth, document number, country, expiry |
| `prebuilt-businessCard` | Business cards | Name, title, company, email, phone, address |
| `prebuilt-tax.us.w2` | US W-2 tax forms | Employer, employee, wages, federal tax withheld |
| `prebuilt-layout` | Any document | Tables, paragraphs, key-value pairs, checkboxes — no specific fields |
| `prebuilt-document` | General documents | Key-value pairs + named entities |
| `prebuilt-read` | Any document | Text only — same output as Computer Vision OCR |

**Rule of thumb:** If your document type has a pre-built model, use it. If not, try `prebuilt-layout`. Only train a custom model when neither covers your needs.

---

### `prebuilt-invoice` — most used in practice

**Where:** Finance, procurement, accounts payable.

| Use case | How |
|---|---|
| Auto-process supplier invoices | Extract vendor, total, line items → push directly into accounting software (SAP, QuickBooks) without manual data entry |
| Invoice matching | Extract PO number from invoice → match against your purchase orders database automatically |
| Audit trail | Extract and store all invoice fields in a database for compliance and auditing |

---

### `prebuilt-receipt` — most used in consumer apps

**Where:** Expense management apps, retail analytics.

| Use case | How |
|---|---|
| Expense reporting | Employee photos a receipt → app extracts merchant, date, total → auto-fills expense report |
| Loyalty programs | Extract items purchased → track what a customer buys over time |
| Returns verification | Verify receipt total and date match before processing a return |

---

### `prebuilt-idDocument` — most used in compliance

**Where:** Banking, fintech, travel, healthcare — anywhere identity verification is required.

| Use case | How |
|---|---|
| KYC (Know Your Customer) | Extract name, DOB, document number from passport or ID → compare against submitted details |
| Age verification | Extract DOB → calculate age → allow or deny access to age-restricted content |
| Hotel check-in | Scan passport on arrival → auto-fill guest registration form |

---

### `prebuilt-layout` — most used in AI / RAG pipelines

**This is the one you've already used in your RAG pipeline.** It is the most versatile model because it works on any document — it does not need to know the document type.

**Where:** RAG pipelines, search indexing, document processing at scale.

| Use case | How |
|---|---|
| **RAG document ingestion** | Send a PDF or Word doc → extract all paragraphs as clean text → chunk and embed for vector search. Layout preserves table structure better than raw OCR. |
| Table extraction for analytics | Extract tables from reports or financial statements → convert to structured data for analysis |
| Search index building | Extract text and key-value pairs from thousands of documents → push to Azure AI Search |
| Form digitisation | Extract any form's key-value pairs without training a custom model — works immediately on any new form type |
| Contract review | Extract all paragraphs from legal contracts → pass to Language service for NER or summarisation |

**Why layout beats raw OCR for RAG:** OCR returns a flat stream of words. Layout returns structured paragraphs and tables with their boundaries preserved — chunks are cleaner, embedding quality is higher, retrieval is more accurate.

---

### `prebuilt-read` — use when you only need text

Same output as the Computer Vision Read API (OCR). Use this if you already have a Document Intelligence resource and don't want to make a separate call to Computer Vision.

---

### Custom models — when nothing fits

The most common real-world scenario: your company has its own forms (internal purchase requests, patient intake forms, customs declarations) that don't match any pre-built model. You collect 5–15 samples, label them in Document Intelligence Studio, train, and call with the same API.

**Most likely exam scenario:** You receive mixed document types in one pipeline — invoices AND receipts AND IDs. Use a **custom classification model** first to decide which document type it is, then route to the right extraction model.

### Custom Models

When no pre-built model fits, train your own.

**Minimum training data:** 5 sample documents (Azure recommends 5–15 for good accuracy).

**Workflow:**
1. Collect sample documents — real examples of the form you want to extract
2. Upload to Azure Blob Storage
3. Label in Document Intelligence Studio (web UI) — draw boxes, name the fields
4. Train the model — Azure fine-tunes a model on your labels
5. Test with new documents
6. Call from Python using your custom model ID (same API call as pre-built)

**Two custom model types:**

| Type | What it does | When to use |
|---|---|---|
| Custom extraction | Extracts specific labelled fields | You have a consistent form layout |
| Custom classification | Decides which document type this is | You receive mixed documents and need to route them |

---

## How It Works — the Poller Pattern

Document Intelligence uses the **long-running operation / poller pattern** — the same as extractive and abstractive summarisation in Stage 04.

Why: analysing a multi-page PDF takes time. You start the job and get a reference back. The SDK polls Azure until it is done, then returns the result.

```
client.begin_analyze_document(...)  ← starts the job, returns a poller
poller.result()                     ← blocks until done, returns the extracted data
```

Every method that analyses a document starts with `begin_`.

---

## The Result Object Structure

After `poller.result()`, you get a result with:

| Attribute | What it contains |
|---|---|
| `result.documents` | List of documents found — one per detected document in the file |
| `result.pages` | Raw page data — text lines, words, positions |
| `result.tables` | Tables extracted from the document |
| `result.key_value_pairs` | Key-value pairs found (layout model) |

For pre-built models, each item in `result.documents` has a `.fields` dictionary. Each key is a field name (`"InvoiceTotal"`, `"VendorName"`) and each value is a field object with:

| Attribute | What it is |
|---|---|
| `.content` | The raw text as it appeared in the document |
| `.valueString` | The value as a plain string |
| `.valueDate` | The value as a date (for date fields) |
| `.valueCurrency` | The value as a currency object (`.amount`, `.currencySymbol`) |
| `.valueArray` | The value as a list (for line items — Items in an invoice) |
| `.valueObject` | A nested object (for each item inside a line item list) |
| `.confidence` | How confident the model is in this field — 0.0 to 1.0 |

---

## Where Document Intelligence is Mostly Used

| Industry | Use case |
|---|---|
| Finance / accounting | Auto-process thousands of supplier invoices — extract totals, vendor names, line items into accounting software without manual entry |
| Retail | Digitise receipts for expense management apps (Expensify, SAP Concur) |
| Healthcare | Extract patient data from admission forms, prescription pads, lab results |
| Government / legal | Process identity documents for KYC (Know Your Customer) compliance — extract passport or ID card fields |
| Insurance | Extract claim forms — policy number, incident date, amount claimed |
| Logistics | Extract shipping labels, bills of lading, customs declarations |
| HR | Parse CVs / resumes — extract name, contact info, work history, education |
| Banking | Process loan applications, account opening forms, tax documents |

---

## AI-102 Exam — Key Points

- Document Intelligence **requires a dedicated resource** — it is not covered by the multi-service account.
- The Terraform resource kind is `"FormRecognizer"` — the old name is still the real kind in Azure even after the service was renamed.
- Pre-built models: know the names — `prebuilt-invoice`, `prebuilt-receipt`, `prebuilt-idDocument`, `prebuilt-layout`, `prebuilt-read`.
- **`prebuilt-layout`** is for any structured document — tables, key-value pairs, no specific field names.
- **`prebuilt-read`** is text-only — same as OCR.
- Minimum **5 training documents** for a custom model.
- **Custom extraction** = extract fields. **Custom classification** = decide what type of document this is.
- The API always uses the **poller pattern** — `begin_analyze_document()` returns a poller, `.result()` blocks until done.
- The SDK package is `azure-ai-documentintelligence` — not `azure-ai-formrecognizer` (the old package name — do not use it).
- Result fields come back as a dictionary — use `.get("FieldName", {})` to avoid key errors on missing fields.
