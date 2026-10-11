# Highly Available E-commerce Web App on AWS

A multi-AZ, auto-scaling web application built on AWS.

![Architecture](architecture.png)

## Services Used
| Service | Purpose |
|---|---|
| Route 53 | DNS and domain routing |
| Application Load Balancer | Distributes traffic across AZs |
| EC2 + Auto Scaling Group | Web/app tier, scales on CPU |
| RDS MySQL | Persistent product data |
| ElastiCache Redis | Caches product queries |
| S3 | Static assets (images) |
| VPC, Security Groups, IAM | Networking and security |

## Architecture Highlights
- **High availability:** EC2 instances in 2 Availability Zones
- **Auto scaling:** Target tracking on 50% CPU (min 2, max 4)
- **Security:** Layered security groups (ALB → EC2 → RDS/Redis); DB and cache in private subnets
- **Performance:** Redis cache reduces DB reads

## Deployment Steps
1. Create VPC with 2 public + 2 private subnets
2. Create security groups
3. Launch RDS MySQL and ElastiCache Redis in private subnets
4. Create S3 bucket and upload images
5. Create IAM role, launch template (user data in `scripts/`)
6. Create target group, ALB and Auto Scaling Group
7. Point Route 53 alias record to the ALB

## Testing
- Refreshing shows different instance/AZ (load balancing)
- Terminated an instance → ASG replaced it (self-healing)
- CPU stress test → scale-out observed

## Screenshots
(add images from /screenshots)

## What I Learned
(write 3-4 bullet points in your own words)

## Future Improvements
- HTTPS with ACM certificate
- Secrets Manager for credentials
- CloudFront in front of S3/ALB
- RDS Multi-AZ failover testing
- Infrastructure as Code (Terraform / CloudFormation)
