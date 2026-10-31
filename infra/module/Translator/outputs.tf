output "endpoint" {
    value = azurerm_cognitive_account.translator.endpoint
}

output "key" {
  value = azurerm_cognitive_account.translator.primary_access_key
  sensitive = true
}

output "region" {
  value = azurerm_cognitive_account.translator.location
}