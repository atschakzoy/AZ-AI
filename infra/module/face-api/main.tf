resource "azurerm_cognitive_account" "face-api" {
  name                  = "face-${var.workload}-${var.environment}"
  resource_group_name   = var.resource_group_name
  location              = var.location
  kind                  = "Face"
  sku_name              = "S0"
  custom_subdomain_name = "face-${var.workload}-${var.environment}"

  identity {
    type = "SystemAssigned"
  }

  network_acls {
    default_action = "Allow"
  }
}