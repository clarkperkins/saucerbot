
locals {
  public_cidr_block = "${cidrsubnet(var.vpc_cidr, 2, 0)}"
  private_cidr_block = "${cidrsubnet(var.vpc_cidr, 2, 1)}"
}


// Create subnets
resource "aws_subnet" "public" {
  vpc_id = "${aws_vpc.main.id}"
  cidr_block = "${cidrsubnet(local.public_cidr_block, 3, count.index)}"
  map_public_ip_on_launch = true

  count = "${length(var.az_list)}"
  availability_zone = "${var.az_list[count.index]}"

  tags = {
    Name = "${var.vpc_name}-public-${var.az_list[count.index]}"
  }
}

resource "aws_subnet" "private" {
  vpc_id = "${aws_vpc.main.id}"
  cidr_block = "${cidrsubnet(local.private_cidr_block, 3, count.index)}"
  map_public_ip_on_launch = false

  count = "${length(var.az_list)}"
  availability_zone = "${var.az_list[count.index]}"

  tags = {
    Name = "${var.vpc_name}-private-${var.az_list[count.index]}"
  }
}
