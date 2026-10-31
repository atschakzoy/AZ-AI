output "endpoint" {
  value = azurerm_cognitive_account.speech.endpoint
}

output "key" {
  value     = azurerm_cognitive_account.speech.primary_access_key
  sensitive = true
}

output "region" {
  value = azurerm_cognitive_account.speech.location
}
