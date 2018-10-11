
// Set up route table for the public subnets
resource "aws_route_table" "public_route" {
  vpc_id = "${aws_vpc.main.id}"

  tags {
    Name = "${var.vpc_name}-public"
  }

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_internet_gateway.main_gateway.id}"
  }
}


// Set up route tables for the private subnets
resource "aws_route_table" "private_route" {
  count = "${length(var.az_list)}"
  vpc_id = "${aws_vpc.main.id}"

  tags {
    Name = "${var.vpc_name}-private-${var.az_list[count.index]}"
  }
}


resource "aws_route_table_association" "public_associate" {
  count = "${length(var.az_list)}"

  subnet_id = "${aws_subnet.public.*.id[count.index]}"
  route_table_id = "${aws_route_table.public_route.id}"
}

resource "aws_route_table_association" "private_associate" {
  count = "${length(var.az_list)}"

  subnet_id = "${aws_subnet.private.*.id[count.index]}"
  route_table_id = "${aws_route_table.private_route.*.id[count.index]}"
}
