variable "location" {
  description = "azure region to deploy resources"
  type        = string
}

variable "environment" {
  description = "environment name (dev,prod)"
  type        = string
}

variable "workload" {
  description = "name of the project"
  type        = string
}
variable "resource_group_name" {
  description = "name of the resource group"
  type        = string
}