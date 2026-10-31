variable "location" {
  description = "location where the resources for translator module woul be deployed in"
  type = string
}

variable "resource_group_name" {
  description = "name of the resource group for the module translator"
  type = string
}

variable "environment" {
  description = "environment of the translator (prod,dev)"
  type = string
}

variable "workload" {
    description = "name of the project"
    type = string
}