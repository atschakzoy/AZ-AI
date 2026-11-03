resource "azurerm_search_service" "search" {
  name                = "search-${var.workload}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "free"
  tags = {
    environment = var.environment
    workload    = var.workload
  }
}