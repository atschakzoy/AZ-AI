resource "azurerm_storage_account" "storage" {
  name                     = "st${var.workload}${var.environment}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags = {
    environment = var.environment
    workload    = var.workload
  }
}

resource "azurerm_storage_container" "documents" {
  name                  = "bst-documents"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}
