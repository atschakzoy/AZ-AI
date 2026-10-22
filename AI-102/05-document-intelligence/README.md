# Stage 05 — Document Intelligence (Form Recognizer)

## What is this and why does it matter?

Every business runs on documents — invoices, receipts, contracts, ID cards, tax forms. Document Intelligence (formerly Form Recognizer) turns those unstructured documents into structured data automatically.

Instead of manually reading a PDF invoice and typing the values into your system, you send the document to this service and get back JSON with all the fields extracted.

---

## What you will learn

- What Document Intelligence does vs plain OCR
- The pre-built models (invoice, receipt, ID document, business card, tax forms)
- The general document and layout models
- Training a custom extraction model
- Calling Document Intelligence from Python

---

## Part 1 — Document Intelligence vs OCR

| OCR (Azure AI Vision Read) | Document Intelligence |
|---------------------------|----------------------|
| Extracts raw text | Extracts structured fields and values |
| Returns words and their positions | Returns "InvoiceTotal: $1,234.56" as a named field |
| No understanding of document structure | Understands tables, key-value pairs, form fields |
| Good for: raw text extraction | Good for: business document processing |

**Example:** An invoice image sent to OCR returns:
```
INVOICE  Invoice #: 12345  Date: 2026-10-01  Total: $500.00
```

The same invoice sent to Document Intelligence returns:
```json
{
  "InvoiceId": "12345",
  "InvoiceDate": "2026-10-01",
  "VendorName": "Contoso Ltd",
  "InvoiceTotal": { "amount": 500.00, "currencySymbol": "$" }
}
```

---

## Part 2 — Pre-built Models

Microsoft has pre-trained models for common document types. Use these first — only train custom models when pre-built doesn't fit.

| Model | Document type | Key fields extracted |
|-------|--------------|---------------------|
| `prebuilt-invoice` | Business invoices | Vendor, customer, line items, totals, tax |
| `prebuilt-receipt` | Retail receipts | Merchant, date, items, total, tip |
| `prebuilt-idDocument` | Passports, driver's licences | Name, DOB, document number, country |
| `prebuilt-businessCard` | Business cards | Name, title, company, email, phone |
| `prebuilt-tax.us.w2` | US W-2 tax forms | Employer, wages, federal tax withheld |
| `prebuilt-layout` | Any document | Tables, paragraphs, key-value pairs, checkboxes |
| `prebuilt-document` | General documents | Key-value pairs + named entities |
| `prebuilt-read` | Any document | Text only (same as Vision OCR) |

---

## Part 3 — Calling Document Intelligence from Python

```bash
pip install azure-ai-documentintelligence azure-identity
```

**Analysing an invoice:**

```python
import os
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.identity import DefaultAzureCredential

client = DocumentIntelligenceClient(
    endpoint=os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"],
    credential=DefaultAzureCredential()
)

# Analyse from URL
poller = client.begin_analyze_document(
    model_id="prebuilt-invoice",
    analyze_request=AnalyzeDocumentRequest(
        url_source="https://example.com/invoice.pdf"
    )
)
result = poller.result()

for invoice in result.documents:
    fields = invoice.fields
    print(f"Vendor: {fields.get('VendorName', {}).get('valueString')}")
    print(f"Invoice ID: {fields.get('InvoiceId', {}).get('valueString')}")
    print(f"Invoice Date: {fields.get('InvoiceDate', {}).get('valueDate')}")
    print(f"Total: {fields.get('InvoiceTotal', {}).get('valueCurrency', {}).get('amount')}")

    # Line items
    items = fields.get("Items", {}).get("valueArray", [])
    for item in items:
        item_fields = item.get("valueObject", {})
        desc = item_fields.get("Description", {}).get("valueString")
        amount = item_fields.get("Amount", {}).get("valueCurrency", {}).get("amount")
        print(f"  Item: {desc} — ${amount}")
```

**Analysing from a local file:**

```python
with open("invoice.pdf", "rb") as f:
    poller = client.begin_analyze_document(
        model_id="prebuilt-invoice",
        analyze_request=f,
        content_type="application/pdf"
    )
result = poller.result()
```

**Analysing a receipt:**

```python
poller = client.begin_analyze_document(
    model_id="prebuilt-receipt",
    analyze_request=AnalyzeDocumentRequest(url_source="https://example.com/receipt.jpg")
)
result = poller.result()

for receipt in result.documents:
    fields = receipt.fields
    print(f"Merchant: {fields.get('MerchantName', {}).get('valueString')}")
    print(f"Total: {fields.get('Total', {}).get('valueCurrency', {}).get('amount')}")
```

---

## Part 4 — Layout Model (Tables and Key-Value Pairs)

The layout model is powerful for documents that do not fit a pre-built model but have clear structure.

```python
poller = client.begin_analyze_document(
    model_id="prebuilt-layout",
    analyze_request=AnalyzeDocumentRequest(url_source="https://example.com/form.pdf")
)
result = poller.result()

# Extract tables
for table in result.tables:
    print(f"Table with {table.row_count} rows, {table.column_count} columns")
    for cell in table.cells:
        print(f"  [{cell.row_index},{cell.column_index}] {cell.content}")

# Extract key-value pairs
for kv_pair in result.key_value_pairs:
    key = kv_pair.key.content if kv_pair.key else ""
    value = kv_pair.value.content if kv_pair.value else ""
    print(f"  {key}: {value}")
```

---

## Part 5 — Custom Models

When your documents are not covered by a pre-built model, train a custom extraction model.

**Workflow:**
1. Collect at least 5 sample documents (PDFs or images)
2. Upload them to Azure Blob Storage
3. Label them in the Document Intelligence Studio (web UI) — draw boxes around fields and name them
4. Train the model
5. Test and iterate
6. Call the model from Python using your custom model ID

**Two custom model types:**
- **Custom extraction** — extract specific fields you label (structured, semi-structured documents)
- **Custom classification** — classify which type of document this is (before routing to the right extraction model)

**Calling a custom model (same pattern as pre-built, just use your model ID):**

```python
poller = client.begin_analyze_document(
    model_id="my-custom-invoice-model",  # your trained model ID
    analyze_request=AnalyzeDocumentRequest(url_source="https://example.com/my-invoice.pdf")
)
result = poller.result()

for doc in result.documents:
    for field_name, field_value in doc.fields.items():
        print(f"{field_name}: {field_value.content}")
```

---

## AI-102 Exam Checklist — Document Intelligence

- [ ] What is the difference between Document Intelligence and plain OCR?
- [ ] Name 4 pre-built models and what they extract
- [ ] When would you use `prebuilt-layout` vs a specific pre-built model?
- [ ] What is the minimum number of documents needed to train a custom model?
- [ ] What is the difference between a custom extraction model and a custom classification model?
- [ ] How do you analyse a local PDF file (not a URL)?
- [ ] What does the `begin_analyze_document` method return? (a poller — it's async)

---

## Exercises

1. Send a real invoice PDF or image to the `prebuilt-invoice` model. Print all extracted fields.
2. Find a receipt image online. Extract the merchant name, date, and total using `prebuilt-receipt`.
3. Scan a document with a table in it. Use `prebuilt-layout` to extract all table cells and print them as a grid.
4. (Advanced) Collect 5+ samples of a custom form (you can make fake ones). Label and train a custom extraction model in Document Intelligence Studio. Call it from Python.
