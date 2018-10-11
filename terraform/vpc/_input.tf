
variable "aws_region" {
  type = "string"
}

variable "az_list" {
  type = "list"
}

variable "domain_name" {
  type = "string"
  default = ""
}

variable "dns_servers" {
  type = "list"
  default = ["AmazonProvidedDNS"]
}

variable "vpc_cidr" {
  type = "string"
}

variable "vpc_name" {
  type = "string"
}
