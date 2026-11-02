variable "location" {
  description = "location where the resources for document intelligence would be deployed"
  type = string
}

variable "resource_group_name" {
  description = "name of the resource group DI would be deployed in"
  type = string
}

variable "workload" {
  description = "name of the project"
  type = string
}

variable "environment" {
  description = "environment of the deployment (prod, dev)"
  type = string
}
