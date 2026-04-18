# EKS Cluster configuration

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "agenticquote-production"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  # Add-ons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  # EKS Managed Node Groups
  eks_managed_node_groups = {
    general = {
      name           = "general"
      instance_types = ["m6i.xlarge", "m5.xlarge"]

      min_size     = 3
      max_size     = 10
      desired_size = 3

      labels = {
        role = "general"
      }

      taints = []
    }

    memory_optimized = {
      name           = "memory-optimized"
      instance_types = ["r6i.xlarge", "r5.xlarge"]

      min_size     = 2
      max_size     = 5
      desired_size = 2

      labels = {
        role = "memory-optimized"
      }

      taints = []
    }
  }

  # IRSA for EBS CSI driver
  irsa_enable = true
}

# Security groups
resource "aws_security_group" "cluster" {
  name_prefix = "agenticquote-cluster"
  vpc_id      = module.vpc.vpc_id

  description = "EKS cluster security group"

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "agenticquote-cluster"
  }
}

resource "aws_security_group" "node" {
  name_prefix = "agenticquote-node"
  vpc_id      = module.vpc.vpc_id

  description = "EKS node security group"

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "agenticquote-node"
  }
}
