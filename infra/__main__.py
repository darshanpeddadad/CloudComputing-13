import json
import pulumi
import pulumi_aws as aws

# Load configurations
config = pulumi.Config()
db_username = config.get("db_username") or "fulda_user"
db_password = config.require_secret("db_password")
db_name = config.get("db_name") or "fulda_app"
domain_name = config.get("domain_name") or "fuldanexus.app"
key_name = config.get("key_name")  # Optional SSH key pair name

# 1. VPC Networking Setup
# Create VPC
vpc = aws.ec2.Vpc(
    "app-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={"Name": "fulda-vpc"},
)

# Create Internet Gateway
igw = aws.ec2.InternetGateway(
    "app-igw",
    vpc_id=vpc.id,
    tags={"Name": "fulda-igw"},
)

# Fetch Availability Zones
azs = aws.get_availability_zones(state="available")
az1 = azs.names[0]
az2 = azs.names[1]

# Create Public Subnets (For EC2 and ALB)
public_subnet_1 = aws.ec2.Subnet(
    "public-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone=az1,
    map_public_ip_on_launch=True,
    tags={"Name": "fulda-public-1"},
)

public_subnet_2 = aws.ec2.Subnet(
    "public-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone=az2,
    map_public_ip_on_launch=True,
    tags={"Name": "fulda-public-2"},
)

# Create Private Subnets (For RDS Database)
private_subnet_1 = aws.ec2.Subnet(
    "private-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone=az1,
    tags={"Name": "fulda-private-1"},
)

private_subnet_2 = aws.ec2.Subnet(
    "private-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.4.0/24",
    availability_zone=az2,
    tags={"Name": "fulda-private-2"},
)

# Route Table for Public Subnets
public_route_table = aws.ec2.RouteTable(
    "public-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
    tags={"Name": "fulda-public-rt"},
)

# Associate Route Table with Public Subnets
aws.ec2.RouteTableAssociation(
    "public-rta-1",
    subnet_id=public_subnet_1.id,
    route_table_id=public_route_table.id,
)

aws.ec2.RouteTableAssociation(
    "public-rta-2",
    subnet_id=public_subnet_2.id,
    route_table_id=public_route_table.id,
)


# 2. Security Groups
# ALB Security Group (Allows web traffic from anywhere)
alb_sg = aws.ec2.SecurityGroup(
    "alb-sg",
    vpc_id=vpc.id,
    description="Security group for Application Load Balancer",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={"Name": "fulda-alb-sg"},
)

# EC2 Security Group (Allows HTTP traffic from ALB, and SSH from anywhere for deployments)
ec2_sg = aws.ec2.SecurityGroup(
    "ec2-sg",
    vpc_id=vpc.id,
    description="Security group for EC2 instances",
    ingress=[
        # HTTP traffic ONLY from the ALB
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            security_groups=[alb_sg.id],
        ),
        # SSH access for deployments / debugging
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={"Name": "fulda-ec2-sg"},
)

# RDS Security Group (Allows MySQL traffic ONLY from EC2)
rds_sg = aws.ec2.SecurityGroup(
    "rds-sg",
    vpc_id=vpc.id,
    description="Security group for RDS instance",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=3306,
            to_port=3306,
            security_groups=[ec2_sg.id],
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={"Name": "fulda-rds-sg"},
)


# 3. S3 Bucket for Media Assets
s3_bucket = aws.s3.BucketV2(
    "app-assets-bucket",
    tags={"Name": "fulda-assets-bucket"},
)

# S3 CORS configuration
s3_cors = aws.s3.BucketCorsConfigurationV2(
    "app-assets-cors",
    bucket=s3_bucket.id,
    cors_rules=[
        aws.s3.BucketCorsConfigurationV2CorsRuleArgs(
            allowed_headers=["*"],
            allowed_methods=["GET", "PUT", "POST", "DELETE", "HEAD"],
            allowed_origins=[f"https://{domain_name}", f"https://www.{domain_name}"],
            expose_headers=["ETag"],
            max_age_seconds=3000,
        )
    ],
)

# Block Public Access Configuration
s3_public_access_block = aws.s3.BucketPublicAccessBlock(
    "app-assets-public-block",
    bucket=s3_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)


# 4. IAM Role for S3 access
iam_role = aws.iam.Role(
    "ec2-s3-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {"Service": "ec2.amazonaws.com"},
                    "Effect": "Allow",
                    "Sid": "",
                }
            ],
        }
    ),
)

# Attach Policy to Role
iam_policy = aws.iam.RolePolicy(
    "ec2-s3-policy",
    role=iam_role.id,
    policy=s3_bucket.id.apply(
        lambda bucket_name: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:DeleteObject",
                            "s3:ListBucket",
                        ],
                        "Resource": [
                            f"arn:aws:s3:::{bucket_name}",
                            f"arn:aws:s3:::{bucket_name}/*",
                        ],
                    }
                ],
            }
        )
    ),
)

instance_profile = aws.iam.InstanceProfile(
    "ec2-profile",
    role=iam_role.name,
)


# 5. RDS MySQL Database
db_subnet_group = aws.rds.SubnetGroup(
    "db-subnet-group",
    subnet_ids=[private_subnet_1.id, private_subnet_2.id],
    tags={"Name": "fulda-db-subnet-group"},
)

db_instance = aws.rds.Instance(
    "mysql-db",
    engine="mysql",
    engine_version="8.0.35",
    instance_class="db.t3.micro",
    allocated_storage=20,
    max_allocated_storage=100,
    db_name=db_name,
    username=db_username,
    password=db_password,
    db_subnet_group_name=db_subnet_group.name,
    vpc_security_group_ids=[rds_sg.id],
    skip_final_snapshot=True,  # Dev/Demo stack convenience. Use False for real production.
    publicly_accessible=False,
    tags={"Name": "fulda-mysql-db"},
)


# 6. ACM SSL Certificate
acm_cert = aws.acm.Certificate(
    "ssl-cert",
    domain_name=domain_name,
    validation_method="DNS",
    subject_alternative_names=[f"www.{domain_name}"],
    tags={"Name": "fulda-acm-certificate"},
)


# 7. EC2 Web Server Instance
# Get latest Ubuntu 22.04 LTS AMI
ubuntu_ami = aws.ec2.get_ami(
    most_recent=True,
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="virtualization-type",
            values=["hvm"],
        ),
    ],
    owners=["099720109477"],  # Canonical owner ID
)

# User data script to configure swap space, install docker, compose, git
user_data = """#!/bin/bash
# 1. Update system packages
apt-get update -y
apt-get upgrade -y

# 2. Allocate 2GB Swap space (helps t3.micro compile React frontend without OOM crashes)
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# 3. Install Docker
apt-get install -y apt-transport-https ca-certificates curl software-properties-common git
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io

# 4. Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# 5. Enable Docker on boot and add ubuntu to docker group
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

echo "✅ Boot strapping completed!"
"""

ec2_instance = aws.ec2.Instance(
    "web-server",
    instance_type="t3.micro",
    ami=ubuntu_ami.id,
    subnet_id=public_subnet_1.id,
    vpc_security_group_ids=[ec2_sg.id],
    iam_instance_profile=instance_profile.name,
    key_name=key_name,
    user_data=user_data,
    tags={"Name": "fulda-web-server"},
)

# Assign Elastic IP
eip = aws.ec2.Eip(
    "web-server-eip",
    instance=ec2_instance.id,
    domain="vpc",
)


# 8. ALB (Application Load Balancer) Setup
alb = aws.lb.LoadBalancer(
    "app-alb",
    internal=False,
    load_balancer_type="application",
    security_groups=[alb_sg.id],
    subnets=[public_subnet_1.id, public_subnet_2.id],
    tags={"Name": "fulda-alb"},
)

# Target Group pointing to EC2 port 80 (where Nginx is listening)
target_group = aws.lb.TargetGroup(
    "app-tg",
    port=80,
    protocol="HTTP",
    vpc_id=vpc.id,
    target_type="instance",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        path="/api/health",  # backend health check route via Nginx proxy
        port="80",
        protocol="HTTP",
        interval=30,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=3,
    ),
    tags={"Name": "fulda-tg"},
)

# Attach EC2 instance to target group
tg_attachment = aws.lb.TargetGroupAttachment(
    "app-tg-attachment",
    target_group_arn=target_group.arn,
    target_id=ec2_instance.id,
    port=80,
)

# HTTP Listener - redirect all port 80 traffic to HTTPS port 443
http_listener = aws.lb.Listener(
    "http-listener",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="redirect",
            redirect=aws.lb.ListenerDefaultActionRedirectArgs(
                port="443",
                protocol="HTTPS",
                status_code="HTTP_301",
            ),
        )
    ],
)

# HTTPS Listener - terminates SSL using ACM Certificate and forwards to Target Group
https_listener = aws.lb.Listener(
    "https-listener",
    load_balancer_arn=alb.arn,
    port=443,
    protocol="HTTPS",
    ssl_policy="ELBSecurityPolicy-2016-08",
    certificate_arn=acm_cert.arn,
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=target_group.arn,
        )
    ],
)


# 9. Stack Exports
pulumi.export("VPC_ID", vpc.id)
pulumi.export("EC2_Public_IP", eip.public_ip)
pulumi.export("RDS_Endpoint", db_instance.endpoint)
pulumi.export("RDS_Address", db_instance.address)
pulumi.export("S3_Bucket_Name", s3_bucket.id)
pulumi.export("ALB_DNS_Name", alb.dns_name)
pulumi.export("ACM_Cert_ARN", acm_cert.arn)

# Export Domain Validation Options for DNS Setup
pulumi.export(
    "Domain_Validation_Options",
    acm_cert.domain_validation_options.apply(
        lambda options: [
            {
                "domain_name": opt.domain_name,
                "resource_record_name": opt.resource_record_name,
                "resource_record_type": opt.resource_record_type,
                "resource_record_value": opt.resource_record_value,
            }
            for opt in options
        ]
    ),
)
