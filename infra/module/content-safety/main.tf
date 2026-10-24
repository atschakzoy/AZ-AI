resource "azurerm_cognitive_account" "content-safety" {
  name                  = "cs-${var.workload}-${var.environment}"
  resource_group_name   = var.resource_group_name
  location              = var.location
  kind                  = "ContentSafety"
  sku_name              = "S0"
  custom_subdomain_name = "cs-${var.workload}-${var.environment}"

  identity {
    type = "SystemAssigned"
  }

  network_acls {
    default_action = "Allow"
    ip_rules       = []
  }
}