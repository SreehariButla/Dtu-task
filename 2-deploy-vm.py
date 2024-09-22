# Import the needed credential and management objects from the libraries.
import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient

print("Provisioning a virtual machine...some operations might take a minute or two.")

# Acquire a credential object.
credential = DefaultAzureCredential()

# Retrieve subscription ID from environment variable.
subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"] = "your-subscription-id"
#subscription_id = "your-subscription-id"

# Constants we need in multiple places: the resource group name and the region in which we provision resources.
RESOURCE_GROUP_NAME = "Data_Engineer"
LOCATION = "westeurope"

# Network and IP address names
VNET_NAME = "Vnet-Sreehari-Butla"
SUBNET_NAME = "subnet-sreehari"
IP_NAME = "ip-example"
IP_CONFIG_NAME = "ip-config-example"
NIC_NAME = "nic-example"
NSG_NAME = "nsg-example"

# Obtain the management object for network resources
network_client = NetworkManagementClient(credential, subscription_id)

# Step 1: Provision a virtual network
poller = network_client.virtual_networks.begin_create_or_update(
    RESOURCE_GROUP_NAME,
    VNET_NAME,
    {
        "location": LOCATION,
        "address_space": {"address_prefixes": ["10.0.0.0/16"]},
    },
)
vnet_result = poller.result()

print(
    f"Provisioned virtual network {vnet_result.name} with address \
prefixes {vnet_result.address_space.address_prefixes}"
)

# Step 2: Create a Network Security Group (NSG)
poller = network_client.network_security_groups.begin_create_or_update(
    RESOURCE_GROUP_NAME,
    NSG_NAME,
    {
        "location": LOCATION,
        "security_rules": [
            {
                "name": "Allow-SSH",
                "protocol": "*",
                "source_port_range": "*",
                "destination_port_range": "22",
                "source_address_prefix": "*",
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 100,
                "direction": "Inbound",
            }
        ],
    },
)
nsg_result = poller.result()

print( f"Provisioned NSG {nsg_result.name} ")

# Step 3: Provision a subnet with NSG
poller = network_client.subnets.begin_create_or_update(
    RESOURCE_GROUP_NAME,
    VNET_NAME,
    SUBNET_NAME,
    {
        "address_prefix": "10.0.0.0/24",
        "network_security_group": {
            "id": nsg_result.id
        },
     },
)
subnet_result = poller.result()

print(
    f"Provisioned subnet {subnet_result.name} with address \
prefix {subnet_result.address_prefix}"
)


# Step 4: Provision a public IP address
poller = network_client.public_ip_addresses.begin_create_or_update(
    RESOURCE_GROUP_NAME,
    IP_NAME,
    {
        "location": LOCATION,
        "sku": {"name": "Basic"},
        "public_ip_allocation_method": "Static",
        "public_ip_address_version": "IPV4",
    },
)
ip_address_result = poller.result()

print(f"Provisioned public IP address {ip_address_result.name} with address {ip_address_result.ip_address}")

# Step 5: Provision the network interface client with the NSG
poller = network_client.network_interfaces.begin_create_or_update(
    RESOURCE_GROUP_NAME,
    NIC_NAME,
    {
        "location": LOCATION,
        "ip_configurations": [
            {
                "name": IP_CONFIG_NAME,
                "subnet": {"id": subnet_result.id},
                "public_ip_address": {"id": ip_address_result.id},
            }
        ],
        "network_security_group": {"id": nsg_result.id},  # Associate the NSG with the NIC
    },
)
nic_result = poller.result()

print(f"Provisioned network interface client {nic_result.name}")

# Step 6: Provision the virtual machine

# Obtain the management object for virtual machines
compute_client = ComputeManagementClient(credential, subscription_id)

VM_NAME = "VM-Sreehari"
USERNAME = "azureuser"
PASSWORD = "Azure@123456"

print(f"Provisioning virtual machine {VM_NAME}; this operation might take a few minutes.")

# Provision the VM specifying only minimal arguments
poller = compute_client.virtual_machines.begin_create_or_update(
    RESOURCE_GROUP_NAME,
    VM_NAME,
    {
        "location": LOCATION,
        "storage_profile": {
            "image_reference": {
                "publisher": "Canonical",
                "offer": "UbuntuServer",
                "sku": "16.04.0-LTS",
                "version": "latest",
            }
        },
        "hardware_profile": {"vm_size": "Standard_DS1_v2"},
        "os_profile": {
            "computer_name": VM_NAME,
            "admin_username": USERNAME,
            "admin_password": PASSWORD,
        },
        "network_profile": {
            "network_interfaces": [
                {
                    "id": nic_result.id,
                }
            ]
        },
    },
)

vm_result = poller.result()

print(f"Provisioned virtual machine {vm_result.name}")