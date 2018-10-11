
resource "aws_vpc" "main" {
  cidr_block = "${var.vpc_cidr}"
  enable_dns_support = true
  enable_dns_hostnames = true

  tags {
    Name = "${var.vpc_name}"
  }
}

// DHCP options
resource "aws_vpc_dhcp_options" "main" {
  domain_name = "${var.domain_name != "" ? var.domain_name : (var.aws_region == "us-east-1" ? "ec2.internal" : format("%s.compute.internal", var.aws_region))}"
  domain_name_servers = ["${var.dns_servers}"]

  tags {
    Name = "${var.vpc_name}"
  }
}

resource "aws_vpc_dhcp_options_association" "main" {
  vpc_id = "${aws_vpc.main.id}"
  dhcp_options_id = "${aws_vpc_dhcp_options.main.id}"
}


resource "aws_internet_gateway" "main_gateway" {
  vpc_id = "${aws_vpc.main.id}"
}

resource "aws_vpc_endpoint" "s3_endpoint" {
    vpc_id = "${aws_vpc.main.id}"
    service_name = "com.amazonaws.${var.aws_region}.s3"
    route_table_ids = [
      "${aws_route_table.public_route.id}",
      "${aws_route_table.private_route.*.id}"
    ]
}
