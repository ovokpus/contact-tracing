variable "region" {
  type    = string
  default = "us-east-1"
}

variable "image_tag" {
  description = "Tag you pushed for every image (see README: Deploy)."
  type        = string
  default     = "v1"
}

variable "es_url" {
  description = "Elasticsearch 8.x endpoint, e.g. an Elastic Cloud deployment URL with credentials (https://user:pass@host:443)."
  type        = string
  sensitive   = true
}
