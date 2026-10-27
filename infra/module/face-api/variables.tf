variable "resource_group_name" {
  description = "name of the resource group"
  type        = string
}

variable "location" {
  description = "location of the face-api model deployment"
  type        = string
}

variable "environment" {
  description = "environment of the projec (prod,dev)"
  type        = string
}

variable "workload" {
  description = "name of the projec"
  type        = string
}