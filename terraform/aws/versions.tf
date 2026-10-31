terraform {
  required_version = ">= 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.71"
    }
  }

  # Remote state (recommended). Create the bucket once with the state module in
  # ovokpus/GKE-Cluster-Management, then uncomment and run `terraform init -migrate-state`.
  # backend "s3" {
  #   bucket       = "<your-state-bucket>"
  #   key          = "contact-tracing/aws.tfstate"
  #   region       = "us-east-1"
  #   use_lockfile = true # S3 native locking; or dynamodb_table = "terraform-locks"
  # }
}
