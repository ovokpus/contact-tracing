output "registry" {
  description = "Push images here (see README: Deploy)."
  value       = module.ecr.registry
}

output "api_url" {
  value = module.api.url
}

output "frontend_url" {
  value = module.frontend.url
}

output "seed_command" {
  value = module.seed.run_command
}
