provider "aws" {
  region = var.region
}

locals {
  instance_type = lookup({
    small  = "t2.micro",
    medium = "t3.small",
    large  = "t3.medium"
  }, var.size, "t2.micro")
}



resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name  = "MainVPC"
    Owner = "erdemir@deloitte.com"
  }
}


resource "aws_subnet" "main" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "eu-west-3a"
  map_public_ip_on_launch = true

  tags = {
    Name  = "MainSubnet"
    Owner = "erdemir@deloitte.com"
  }
}


resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name  = "MainInternetGateway"
    Owner = "erdemir@deloitte.com"
  }
}


resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name  = "PublicRouteTable"
    Owner = "erdemir@deloitte.com"
  }
}


resource "aws_route_table_association" "public_subnet_association" {
  subnet_id      = aws_subnet.main.id
  route_table_id = aws_route_table.public.id
}


resource "aws_security_group" "env_sg" {
  name        = "${var.env_name}_sg"
  description = "Allow SSH, HTTP, 8080, 9090"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name  = "${var.env_name}-sg"
    Owner = "erdemir@deloitte.com"
  }
}


resource "aws_instance" "env" {
  ami                    = var.ami_id
  instance_type          = local.instance_type
  key_name               = var.key_name
  subnet_id              = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.env_sg.id]
  associate_public_ip_address = true

  tags = {
    Name     = var.env_name
    Template = var.template
    Owner = "erdemir@deloitte.com"
  }
}

resource "aws_eip" "env_ip" {
  instance = aws_instance.env.id
  domain   = "vpc"

  tags = {
    Name = "${var.env_name}-eip"
    Owner = "erdemir@deloitte.com"
  }
}
