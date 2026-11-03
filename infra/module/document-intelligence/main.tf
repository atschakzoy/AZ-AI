resource "azurerm_cognitive_account" "document_intelligence" {
  name                  = "di-${var.workload}-${var.environment}"
  resource_group_name   = var.resource_group_name
  location              = var.location
  kind                  = "FormRecognizer"
  sku_name              = "F0"
  custom_subdomain_name = "di-${var.workload}-${var.environment}"

  tags = {
    environment = var.environment
    workload    = var.workload

  }
}