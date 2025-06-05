output "instance_ip" {
  value = aws_eip.env_ip.public_ip
}
