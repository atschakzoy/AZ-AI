output "endpoint" {
  value = azurerm_cognitive_account.openai.endpoint
}   

output "key" {
  value = azurerm_cognitive_account.openai.primary_access_key
  sensitive = true
}