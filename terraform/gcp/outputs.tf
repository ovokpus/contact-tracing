output "registry" {
  description = "Push images here (see README: Deploy)."
  value       = module.registry.repository_url
}

output "api_url" {
  value = module.api.url
}

output "frontend_url" {
  value = module.frontend.url
}

output "seed_command" {
  value = module.seed.execute_command
}
