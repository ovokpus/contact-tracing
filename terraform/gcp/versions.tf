terraform {
  required_version = ">= 1.9"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.9"
    }
  }

  # Remote state (recommended). Create the bucket once with the state module in
  # ovokpus/GKE-Cluster-Management, then uncomment and run `terraform init -migrate-state`.
  # backend "gcs" {
  #   bucket = "<your-state-bucket>"
  #   prefix = "contact-tracing/gcp"
  # }
}
