variable "env_name" {
  description = "Name of the environment"
  type        = string
}

variable "template" {
  description = "Type of environment (web, db, fullstack)"
  type        = string
}

variable "size" {
  description = "Instance size (small, medium, large)"
  type        = string
}

variable "region" {
  description = "AWS Region"
  default     = "eu-west-3"
}

variable "ami_id" {
  description = "AMI ID for EC2 (Ubuntu 20.04 Paris)"
  default     = "ami-01d21b7be69801c2f"
}

variable "key_name" {
  description = "AWS EC2 Key Pair name"
  default     = "erdemir-paris-key"
}
