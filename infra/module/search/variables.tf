variable "location" {
  description = "location of the search services would be deployed"
  type        = string
}

variable "resource_group_name" {
  description = "name of the resource group which search services would be in"
  type        = string
}

variable "workload" {
  description = "name of the project "
  type        = string
}

variable "environment" {
  description = "environment of the deployment (prod, dev)"
}