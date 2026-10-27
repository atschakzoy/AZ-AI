resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.workload}-${var.environment}"
  location = var.location
}

module "foundry-tools" {
  source              = "./module/foundry-tools"
  location            = var.location
  environment         = var.environment
  workload            = var.workload
  resource_group_name = azurerm_resource_group.rg.name
}

module "content-safety" {
  source              = "./module/content-safety"
  location            = var.location
  environment         = var.environment
  workload            = var.workload
  resource_group_name = azurerm_resource_group.rg.name
}

module "computer-vision" {
  source              = "./module/computer-vision"
  location            = var.location
  environment         = var.environment
  workload            = var.workload
  resource_group_name = azurerm_resource_group.rg.name
}

module "face-api" {
  source = "./module/face-api"
  location = var.location
  environment = var.environment
  workload = var.workload
  resource_group_name = azurerm_resource_group.rg.name
}