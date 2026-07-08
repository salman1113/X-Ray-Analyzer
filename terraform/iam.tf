# Setup OIDC Provider for GitHub Actions
module "github_oidc" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-github-oidc-provider"
  version = "~> 5.0"
}

resource "aws_iam_policy" "eks_admin" {
  name        = "github-actions-eks-admin-policy"
  description = "Allows GitHub Actions to describe and access EKS cluster"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "eks:DescribeCluster",
          "eks:ListClusters",
          "eks:AccessKubernetesApi"
        ]
        Resource = "*"
      }
    ]
  })
}

module "iam_github_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-github-oidc-role"
  version = "~> 5.0"

  name = "github-actions-deploy-role"

  # Replace with the user's actual GitHub repository name (e.g., "username/repo")
  subjects = ["repo:jithin-jz/X-Ray-Analyzer:*"]

  policies = {
    ECRPushPull = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser"
    EKSAdmin    = aws_iam_policy.eks_admin.arn
  }
}

output "github_actions_role_arn" {
  value = module.iam_github_role.arn
}

resource "aws_eks_access_entry" "github_actions" {
  cluster_name      = var.cluster_name
  principal_arn     = module.iam_github_role.arn
}

resource "aws_eks_access_policy_association" "github_actions_admin" {
  cluster_name  = var.cluster_name
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
  principal_arn = module.iam_github_role.arn

  access_scope {
    type = "cluster"
  }
}

