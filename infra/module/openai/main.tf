resource "azurerm_cognitive_account" "openai" {
  name = "oai-${var.workload}-${var.environment}"
  resource_group_name = var.resource_group_name
  location = var.location
  kind = "OpenAI"
  sku_name = "S0"

  tags = {
    environment = var.environment
    workload = var.workload
  }
}

resource "azurerm_cognitive_deployment" "gpt4o" {
  name = "gpt-4o"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format = "OpenAI"
    name = "gpt-4o"
    version = "2024-11-20"
  }
  
  scale {
    type     = "Standard"
    capacity = 10
  }
}

resource "azurerm_cognitive_deployment" "embedding" {
  name                 = "text-embedding-3-small"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-small"
    version = "1"
  }

  scale {
    type     = "Standard"
    capacity = 10
  }
}

