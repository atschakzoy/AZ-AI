resource "azurerm_cognitive_account" "custom-vision-training" {
  name                = "cv-training-${var.workload}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = "CustomVision.Training"
  sku_name            = "F0"

  identity {
    type = "SystemAssigned"
  }

}

resource "azurerm_cognitive_account" "custom-vision-prediction" {
  name                = "cv-prediction-${var.workload}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  kind                = "CustomVision.Prediction"
  sku_name            = "F0"

  identity {
    type = "SystemAssigned"
  }

}
