provider "aws" {
  region = var.region
  default_tags {
    tags = { app = "contact-tracing", managed-by = "terraform" }
  }
}

# Default VPC keeps the example small. Use a dedicated VPC for production.
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_security_group" "app" {
  name_prefix = "tracer-app-"
  description = "contact-tracing tasks"
  vpc_id      = data.aws_vpc.default.id
}

resource "aws_vpc_security_group_ingress_rule" "app_80" {
  security_group_id = aws_security_group.app.id
  description       = "load balancer to tasks"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = data.aws_vpc.default.cidr_block
}

resource "aws_vpc_security_group_ingress_rule" "app_8000" {
  security_group_id = aws_security_group.app.id
  description       = "load balancer to tasks"
  ip_protocol       = "tcp"
  from_port         = 8000
  to_port           = 8000
  cidr_ipv4         = data.aws_vpc.default.cidr_block
}

resource "aws_vpc_security_group_egress_rule" "app_all" {
  security_group_id = aws_security_group.app.id
  description       = "outbound (image pulls, database, external APIs)"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_ecs_cluster" "this" {
  name = "tracer"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_secretsmanager_secret" "var_es_url" {
  name_prefix = "tracer-var-es-url-"
}

resource "aws_secretsmanager_secret_version" "var_es_url" {
  secret_id     = aws_secretsmanager_secret.var_es_url.id
  secret_string = var.es_url
}

module "ecr" {
  source = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/aws/ecr?ref=tf-modules-v0.1.0"
  prefix = "tracer"
  names  = ["app", "frontend"]
}

module "api" {
  source             = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/aws/express-service?ref=tf-modules-v0.1.0"
  name               = "tracer-api"
  cluster            = aws_ecs_cluster.this.name
  image              = "${module.ecr.repository_urls["app"]}:${var.image_tag}"
  port               = 8000
  health_path        = "/health"
  subnet_ids         = data.aws_subnets.default.ids
  security_group_ids = [aws_security_group.app.id]
  env = {
    SCANS_INDEX      = "app_scans"
    BUSINESSES_INDEX = "businesses"
  }
  secret_env = {
    ES_URL = aws_secretsmanager_secret.var_es_url.arn
  }
}

module "frontend" {
  source             = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/aws/express-service?ref=tf-modules-v0.1.0"
  name               = "tracer-frontend"
  cluster            = aws_ecs_cluster.this.name
  image              = "${module.ecr.repository_urls["frontend"]}:${var.image_tag}"
  port               = 80
  health_path        = "/"
  subnet_ids         = data.aws_subnets.default.ids
  security_group_ids = [aws_security_group.app.id]
  env = {
    API_UPSTREAM = module.api.url
  }
  secret_env = {}
}

module "seed" {
  source             = "git::https://github.com/ovokpus/GKE-Cluster-Management.git//terraform/modules/aws/fargate-job?ref=tf-modules-v0.1.0"
  name               = "tracer-seed"
  cluster            = aws_ecs_cluster.this.name
  image              = "${module.ecr.repository_urls["app"]}:${var.image_tag}"
  command            = ["python", "-m", "tracer.seed"]
  subnet_ids         = data.aws_subnets.default.ids
  security_group_ids = [aws_security_group.app.id]
  env = {
    SCANS_INDEX      = "app_scans"
    BUSINESSES_INDEX = "businesses"
    SYNTH_BUSINESSES = "600"
    SYNTH_PEOPLE     = "2500"
    SYNTH_DAYS       = "3"
  }
  secret_env = {
    ES_URL = aws_secretsmanager_secret.var_es_url.arn
  }
}
