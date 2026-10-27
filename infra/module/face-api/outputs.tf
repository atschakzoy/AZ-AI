output "face_endpoint" {
  value = azurerm_cognitive_account.face-api.endpoint
}

output "face_key" {
  value     = azurerm_cognitive_account.face-api.primary_access_key
  sensitive = true
}