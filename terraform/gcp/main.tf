provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "secretmanager" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_secret_manager_secret" "var_es_url" {
  secret_id = "tracer-var-es-url"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "var_es_url" {
  secret      = google_secret_manager_secret.var_es_url.id
  secret_data = var.es_url
}

module "registry" {
  source        = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/gcp/artifact-registry?ref=tf-modules-v0.1.0"
  project_id    = var.project_id
  region        = var.region
  repository_id = "tracer"
}

module "api" {
  source      = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/gcp/cloud-run-service?ref=tf-modules-v0.1.0"
  project_id  = var.project_id
  region      = var.region
  name        = "tracer-api"
  image       = "${module.registry.repository_url}/app:${var.image_tag}"
  port        = 8000
  memory      = "512Mi"
  health_path = "/health"
  env = {
    SCANS_INDEX      = "app_scans"
    BUSINESSES_INDEX = "businesses"
  }
  secret_env = {
    ES_URL = google_secret_manager_secret.var_es_url.secret_id
  }
}

module "frontend" {
  source      = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/gcp/cloud-run-service?ref=tf-modules-v0.1.0"
  project_id  = var.project_id
  region      = var.region
  name        = "tracer-frontend"
  image       = "${module.registry.repository_url}/frontend:${var.image_tag}"
  port        = 80
  memory      = "512Mi"
  health_path = "/"
  env = {
    API_UPSTREAM = module.api.url
  }
  secret_env = {}
}

module "seed" {
  source     = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/gcp/cloud-run-job?ref=tf-modules-v0.1.0"
  project_id = var.project_id
  region     = var.region
  name       = "tracer-seed"
  image      = "${module.registry.repository_url}/app:${var.image_tag}"
  memory     = "1Gi"
  command    = ["python", "-m", "tracer.seed"]
  env = {
    SCANS_INDEX      = "app_scans"
    BUSINESSES_INDEX = "businesses"
    SYNTH_BUSINESSES = "600"
    SYNTH_PEOPLE     = "2500"
    SYNTH_DAYS       = "3"
  }
  secret_env = {
    ES_URL = google_secret_manager_secret.var_es_url.secret_id
  }
}
