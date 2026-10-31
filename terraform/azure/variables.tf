variable "location" {
  type    = string
  default = "canadacentral"
}

variable "name_prefix" {
  description = "Lowercase letters/digits; used for globally unique names (ACR, Postgres)."
  type        = string
  default     = "tracer"
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
