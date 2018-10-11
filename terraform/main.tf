terraform {
  backend "s3" {
    bucket = "clarkperkins-terraform-state"
    key = "apps/saucerbot.tfstate"
    region = "us-east-1"
    profile = "clarkperkins"
  }
}

provider "aws" {
  region = "us-east-1"
  profile = "clarkperkins"
}

module "vpc" {
  source = "vpc"

  vpc_name = "saucerbot"
  aws_region = "us-east-1"
  vpc_cidr = "10.7.0.0/20"
  az_list = [
    "us-east-1a",
    "us-east-1b",
    "us-east-1c",
    "us-east-1d",
    "us-east-1e",
    "us-east-1f"
  ]
}