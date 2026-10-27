variable "location" {
  description = "the location of the resources being deployed"
  type        = string
}

variable "environment" {
  description = "environment of the resource (Prod,dev)"
  type        = string
}

variable "workload" {
  description = "the name of the project"
  type        = string
}

variable "resource_group_name" {
  description = "the resource group where the resource will be deployed in"
  type        = string
}
