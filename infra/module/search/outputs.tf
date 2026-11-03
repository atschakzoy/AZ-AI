output "endpoint" {
  value = "https://${azurerm_search_service.search.name}.search.windows.net"

}

output "key" {
  value     = azurerm_search_service.search.primary_key
  sensitive = true
}