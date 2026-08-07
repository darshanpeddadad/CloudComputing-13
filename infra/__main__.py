import json
import pulumi
import pulumi_openstack as openstack

config = pulumi.Config()
db_username = config.get("db_username") or "fulda_user"
db_password = config.require_secret("db_password")
db_name = config.get("db_name") or "fulda_app"
domain_name = config.get("domain_name") or "fuldanexus.app"
key_name = config.get("key_name") or "CloudComp13-keypair"
flavor_name = config.get("flavor_name") or "m1.small"
image_name = config.get("image_name") or "ubuntu-22.04-jammy-server-cloud-image-amd64"
external_network_name = config.get("external_network_name") or "ext_net"

ext_net = openstack.networking.get_network(name=external_network_name)

network = openstack.networking.Network(
    "app-network",
    name="fulda-network",
    admin_state_up=True,
    tags=["fulda-app"]
)

subnet = openstack.networking.Subnet(
    "app-subnet",
    name="fulda-subnet",
    network_id=network.id,
    cidr="10.0.1.0/24",
    ip_version=4,
    dns_nameservers=["8.8.8.8", "8.8.4.4"],
    tags=["fulda-app"]
)

router = openstack.networking.Router(
    "app-router",
    name="fulda-router",
    external_network_id=ext_net.id,
    admin_state_up=True,
    tags=["fulda-app"]
)

router_interface = openstack.networking.RouterInterface(
    "app-router-interface",
    router_id=router.id,
    subnet_id=subnet.id
)

secgroup_web = openstack.networking.SecGroup(
    "secgroup-web",
    name="fulda-secgroup-web",
    description="Security group for web instances (HTTP, HTTPS, SSH)"
)

rule_ssh = openstack.networking.SecGroupRule(
    "rule-ssh",
    direction="ingress",
    ethertype="IPv4",
    protocol="tcp",
    port_range_min=22,
    port_range_max=22,
    remote_ip_prefix="0.0.0.0/0",
    security_group_id=secgroup_web.id
)

rule_http = openstack.networking.SecGroupRule(
    "rule-http",
    direction="ingress",
    ethertype="IPv4",
    protocol="tcp",
    port_range_min=80,
    port_range_max=80,
    remote_ip_prefix="0.0.0.0/0",
    security_group_id=secgroup_web.id
)

rule_https = openstack.networking.SecGroupRule(
    "rule-https",
    direction="ingress",
    ethertype="IPv4",
    protocol="tcp",
    port_range_min=443,
    port_range_max=443,
    remote_ip_prefix="0.0.0.0/0",
    security_group_id=secgroup_web.id
)

secgroup_db = openstack.networking.SecGroup(
    "secgroup-db",
    name="fulda-secgroup-db",
    description="Security group for DB instance (MySQL)"
)

rule_mysql = openstack.networking.SecGroupRule(
    "rule-mysql",
    direction="ingress",
    ethertype="IPv4",
    protocol="tcp",
    port_range_min=3306,
    port_range_max=3306,
    remote_group_id=secgroup_web.id,
    security_group_id=secgroup_db.id
)

swift_container = openstack.objectstorage.Container(
    "app-assets-container",
    name="fulda-assets",
    container_read=".r:*,.rlistings",
)

db_user_data = pulumi.Output.all(db_name=db_name, db_user=db_username, db_pass=db_password).apply(
    lambda args: f"""#!/bin/bash
apt-get update -y
apt-get upgrade -y
apt-get install -y mysql-server
sed -i 's/bind-address.*/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
systemctl restart mysql
mysql -e "CREATE DATABASE IF NOT EXISTS {args['db_name']};"
mysql -e "CREATE USER IF NOT EXISTS '{args['db_user']}'@'%' IDENTIFIED BY '{args['db_pass']}';"
mysql -e "GRANT ALL PRIVILEGES ON {args['db_name']}.* TO '{args['db_user']}'@'%';"
mysql -e "FLUSH PRIVILEGES;"
"""
)

db_port = openstack.networking.Port(
    "db-server-port",
    name="fulda-db-server-port",
    network_id=network.id,
    security_group_ids=[secgroup_db.id],
    opts=pulumi.ResourceOptions(depends_on=[subnet])
)

db_instance = openstack.compute.Instance(
    "db-server",
    name="fulda-db-server",
    flavor_name=flavor_name,
    image_name=image_name,
    key_pair=key_name,
    networks=[{"port": db_port.id}],
    user_data=db_user_data,
    tags=["fulda-app"],
    opts=pulumi.ResourceOptions(depends_on=[router_interface])
)

web_user_data = """#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
apt-get install -y apt-transport-https ca-certificates curl software-properties-common git
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu
git clone https://github.com/darshanpeddadad/CloudComputing-13.git /home/ubuntu/app
chown -R ubuntu:ubuntu /home/ubuntu/app
echo "Web bootstrapping completed!" >> /var/log/cloud-init-fulda.log
"""

instance_count = config.get_int("instance_count") or 1
web_ports = []
web_instances = []

for i in range(instance_count):
    web_port = openstack.networking.Port(
        f"web-server-port-{i}",
        name=f"fulda-web-server-port-{i}",
        network_id=network.id,
        security_group_ids=[secgroup_web.id],
        opts=pulumi.ResourceOptions(depends_on=[subnet])
    )
    web_ports.append(web_port)

    web_instance = openstack.compute.Instance(
        f"web-server-{i}",
        name=f"fulda-web-server-{i}",
        flavor_name=flavor_name,
        image_name=image_name,
        key_pair=key_name,
        networks=[{"port": web_port.id}],
        user_data=web_user_data,
        tags=["fulda-app"],
        opts=pulumi.ResourceOptions(depends_on=[router_interface])
    )
    web_instances.append(web_instance)

floating_ip = openstack.networking.FloatingIp(
    "web-server-fip",
    pool=external_network_name
)

fip_association = openstack.networking.FloatingIpAssociate(
    "web-server-fip-assoc",
    floating_ip=floating_ip.address,
    port_id=web_ports[0].id,
    opts=pulumi.ResourceOptions(depends_on=[router_interface, web_instances[0]])
)

pulumi.export("Network_ID", network.id)
pulumi.export("Subnet_ID", subnet.id)
pulumi.export("Router_ID", router.id)
pulumi.export(
    "DB_Private_IP",
    db_port.all_fixed_ips.apply(lambda ips: ips[0] if ips else None)
)
pulumi.export("Web_Primary_Public_IP", floating_ip.address)
pulumi.export(
    "Web_Private_IPs",
    pulumi.Output.all(*[
        port.all_fixed_ips.apply(lambda ips: ips[0] if ips else None)
        for port in web_ports
    ])
)
pulumi.export("Swift_Container_Name", swift_container.name)
