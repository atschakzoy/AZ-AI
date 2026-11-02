import os
from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential

load_dotenv()

endpoint = os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"]
key = os.environ["DOCUMENT_INTELLIGENCE_KEY"]

client = DocumentIntelligenceClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

invoice_url = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/sample-invoice.pdf"

poller = client.begin_analyze_document(
    model_id="prebuilt-invoice",
    body=AnalyzeDocumentRequest(url_source=invoice_url)
)

result = poller.result()

for doc in result.documents:
    fields = doc.fields

    print(fields.get("VendorName").content)
    print(fields.get("InvoiceId").content)
    print(fields.get("InvoiceTotal").content)


print("-----------------------")

receipt_url = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/contoso-allinone.jpg"

poller2 = client.begin_analyze_document(
    model_id="prebuilt-receipt",
    body=AnalyzeDocumentRequest(url_source=receipt_url)
)

result2 = poller2.result()

for doc in result2.documents:
    fields = doc.fields
    print(fields.get("MerchantName").content)
    print(fields.get("TransactionDate").content)
    print(fields.get("Total").content)


print("-----------------------")

layout_url = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/sample-invoice.pdf"

poller3 = client.begin_analyze_document(
    model_id="prebuilt-layout",
    body=AnalyzeDocumentRequest(url_source=layout_url)
)

result3 = poller3.result()

for table in result3.tables:
    print(f"Table: {table.row_count} rows x {table.column_count} columns")
    for cell in table.cells:
        print(f"  [{cell.row_index},{cell.column_index}] {cell.content}")
    