variable "location" {
  description = "where the resources for speech would be deployed"
  type = string
}

variable "resource_group_name" {
  description = "name of the resource group for speech"
  type = string
}

variable "environment" {
  description = "environment of speech (prod,dev)"
  type = string
}

variable "workload" {
    description = "name of the project"
    type = string
}