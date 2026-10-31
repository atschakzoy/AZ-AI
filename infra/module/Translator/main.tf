resource "azurerm_cognitive_account" "translator" {
  name = "translator-${var.workload}-${var.environment}"
  resource_group_name = var.resource_group_name
  location = var.location
  kind = "TextTranslation"
  sku_name = "F0"


tags = {
    environment = var.environment
    workload = var.workload
}
}