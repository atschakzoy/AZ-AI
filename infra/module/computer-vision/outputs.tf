output "training_endpoint" {
  value = azurerm_cognitive_account.custom-vision-training.endpoint
}

output "training_key" {
  value     = azurerm_cognitive_account.custom-vision-training.primary_access_key
  sensitive = true
}

output "prediction_endpoint" {
  value = azurerm_cognitive_account.custom-vision-prediction.endpoint
}

output "prediction_key" {
  value     = azurerm_cognitive_account.custom-vision-prediction.primary_access_key
  sensitive = true
}

output "prediction_resource_id" {
  value = azurerm_cognitive_account.custom-vision-prediction.id
}