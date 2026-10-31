provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "this" {
  name     = "rg-tracer"
  location = var.location
}

module "acr" {
  source              = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/azure/acr?ref=tf-modules-v0.1.0"
  resource_group_name = azurerm_resource_group.this.name
  location            = var.location
  name                = "${var.name_prefix}acr"
}

module "env" {
  source              = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/azure/container-apps-env?ref=tf-modules-v0.1.0"
  resource_group_name = azurerm_resource_group.this.name
  location            = var.location
  name                = "cae-tracer"
  acr_id              = module.acr.id
}

module "api" {
  source              = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/azure/container-app?ref=tf-modules-v0.1.0"
  resource_group_name = azurerm_resource_group.this.name
  name                = "tracer-api"
  environment_id      = module.env.id
  identity_id         = module.env.identity_id
  registry_server     = module.acr.login_server
  image               = "${module.acr.login_server}/app:${var.image_tag}"
  port                = 8000
  env = {
    SCANS_INDEX      = "app_scans"
    BUSINESSES_INDEX = "businesses"
  }
  secret_env = {
    ES_URL = var.es_url
  }
}

module "frontend" {
  source              = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/azure/container-app?ref=tf-modules-v0.1.0"
  resource_group_name = azurerm_resource_group.this.name
  name                = "tracer-frontend"
  environment_id      = module.env.id
  identity_id         = module.env.identity_id
  registry_server     = module.acr.login_server
  image               = "${module.acr.login_server}/frontend:${var.image_tag}"
  port                = 80
  env = {
    API_UPSTREAM = module.api.url
  }
  secret_env = {}
}

module "seed" {
  source              = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/azure/container-app-job?ref=tf-modules-v0.1.0"
  resource_group_name = azurerm_resource_group.this.name
  location            = var.location
  name                = "tracer-seed"
  environment_id      = module.env.id
  identity_id         = module.env.identity_id
  registry_server     = module.acr.login_server
  image               = "${module.acr.login_server}/app:${var.image_tag}"
  command             = ["python", "-m", "tracer.seed"]
  env = {
    SCANS_INDEX      = "app_scans"
    BUSINESSES_INDEX = "businesses"
    SYNTH_BUSINESSES = "600"
    SYNTH_PEOPLE     = "2500"
    SYNTH_DAYS       = "3"
  }
  secret_env = {
    ES_URL = var.es_url
  }
}
