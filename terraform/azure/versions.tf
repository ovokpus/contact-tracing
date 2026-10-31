terraform {
  required_version = ">= 1.9"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.12"
    }
  }

  # Remote state (recommended). Create the bucket once with the state module in
  # ovokpus/GKE-Cluster-Management, then uncomment and run `terraform init -migrate-state`.
  # backend "azurerm" {
  #   resource_group_name  = "<state-rg>"
  #   storage_account_name = "<statestorageacct>"
  #   container_name       = "tfstate"
  #   key                  = "contact-tracing/azure.tfstate"
  #   use_azuread_auth     = true
  # }
}
