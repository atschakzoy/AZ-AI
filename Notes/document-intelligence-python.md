# Document Intelligence — Python Patterns

Quick reference for writing Python scripts that call Azure AI Document Intelligence.

---

## Install

```bash
pip install azure-ai-documentintelligence
```

---

## Imports

```python
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
```

- `DocumentIntelligenceClient` — the client class, one per script
- `AnalyzeDocumentRequest` — wraps the input (URL or bytes) before sending to the API
- `AzureKeyCredential` — key-based auth for local development

---

## Client Setup

```python
import os
from dotenv import load_dotenv

load_dotenv()

endpoint = os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"]
key = os.environ["DOCUMENT_INTELLIGENCE_KEY"]

client = DocumentIntelligenceClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)
```

---

## Analyse from a URL

```python
poller = client.begin_analyze_document(
    model_id="prebuilt-invoice",
    body=AnalyzeDocumentRequest(url_source="https://example.com/invoice.pdf")
)
result = poller.result()
```

- `model_id` — which model to use. Any pre-built model ID or your custom model ID.
- `body` — wraps the input (URL or file). Note: older docs and tutorials show `analyze_request=` — the newer SDK uses `body=` instead.
- `url_source` — a publicly accessible URL to the document. Azure fetches it directly.
- `poller.result()` — blocks until the analysis is complete, returns the result object.

---

## Analyse from a Local File

```python
with open("invoice.pdf", "rb") as f:
    poller = client.begin_analyze_document(
        model_id="prebuilt-invoice",
        body=f,
        content_type="application/pdf"
    )
result = poller.result()
```

- `"rb"` — read binary mode. Documents are binary files, not text.
- `content_type` — must match the file type. Use `"application/pdf"` for PDFs, `"image/jpeg"` for JPGs, `"image/png"` for PNGs.

---

## Reading Fields — Pre-built Models

Every pre-built model (except layout) returns `result.documents` — a list of documents. Each document has a `.fields` dictionary.

```python
for doc in result.documents:
    fields = doc.fields

    # Safe way to get a value — .get() returns None if the field is missing
    vendor = fields.get("VendorName")
    if vendor:
        print(vendor.content)         # raw text as it appeared
        print(vendor.value_string)    # same, but typed as string
        print(vendor.confidence)      # 0.0 to 1.0
```

### Field value types — which attribute to use

| Field type | Attribute | Example |
|---|---|---|
| Text | `.value_string` | `"Contoso Ltd"` |
| Date | `.value_date` | `datetime.date(2026, 10, 1)` |
| Number | `.value_number` | `42.5` |
| Currency | `.value_currency` | object with `.amount` and `.currency_symbol` |
| List (line items) | `.value_array` | list of item objects |
| Nested object | `.value_object` | dict of sub-fields |
| Raw text always | `.content` | whatever text appeared on the page |

---

## Invoice — Common Fields

```python
for doc in result.documents:
    fields = doc.fields

    print(fields.get("InvoiceId").content if fields.get("InvoiceId") else "")
    print(fields.get("VendorName").content if fields.get("VendorName") else "")
    print(fields.get("InvoiceDate").content if fields.get("InvoiceDate") else "")

    # Currency field
    total = fields.get("InvoiceTotal")
    if total and total.value_currency:
        print(total.value_currency.amount)
        print(total.value_currency.currency_symbol)

    # Line items — valueArray → list of objects → each object has sub-fields
    items = fields.get("Items")
    if items and items.value_array:
        for item in items.value_array:
            sub = item.value_object or {}
            desc = sub.get("Description")
            amount = sub.get("Amount")
            print(desc.content if desc else "", amount.content if amount else "")
```

---

## Receipt — Common Fields

```python
for doc in result.documents:
    fields = doc.fields
    print(fields.get("MerchantName").content if fields.get("MerchantName") else "")
    print(fields.get("TransactionDate").content if fields.get("TransactionDate") else "")

    total = fields.get("Total")
    if total and total.value_currency:
        print(total.value_currency.amount)
```

---

## ID Document — Common Fields

```python
for doc in result.documents:
    fields = doc.fields
    print(fields.get("FirstName").content if fields.get("FirstName") else "")
    print(fields.get("LastName").content if fields.get("LastName") else "")
    print(fields.get("DateOfBirth").content if fields.get("DateOfBirth") else "")
    print(fields.get("DocumentNumber").content if fields.get("DocumentNumber") else "")
    print(fields.get("CountryRegion").content if fields.get("CountryRegion") else "")
```

---

## Layout Model — Tables and Key-Value Pairs

Layout model does not use `result.documents`. It uses `result.tables` and `result.key_value_pairs`.

```python
# Tables
for table in result.tables:
    print(f"Table: {table.row_count} rows x {table.column_count} columns")
    for cell in table.cells:
        print(f"  [{cell.row_index},{cell.column_index}] {cell.content}")

# Key-value pairs
for kv in result.key_value_pairs:
    key = kv.key.content if kv.key else ""
    value = kv.value.content if kv.value else ""
    print(f"{key}: {value}")
```

---

## Custom Model — same pattern, different model_id

```python
poller = client.begin_analyze_document(
    model_id="your-custom-model-id",
    analyze_request=AnalyzeDocumentRequest(url_source="https://example.com/doc.pdf")
)
result = poller.result()

for doc in result.documents:
    for field_name, field_value in doc.fields.items():
        print(field_name, field_value.content)
```

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `ResourceNotFound` | Wrong endpoint URL | Check `.env` — must be the Document Intelligence endpoint, not the Foundry endpoint |
| `AuthenticationFailed` | Wrong key | Check `.env` key matches the Document Intelligence resource |
| `InvalidRequest` | URL not accessible | Azure must be able to reach the URL — use a public URL or local file instead |
| `content_type` missing | Local file analysis fails | Always pass `content_type` when using a local file |
| `KeyError` on field | Field not found in document | Use `.get("FieldName")` and check `if field:` before reading the value |
| `None` on `.value_currency` | Field exists but value is empty | Always check `if field and field.value_currency:` before accessing amount |
