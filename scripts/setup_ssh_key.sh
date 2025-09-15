#!/bin/bash
# SSH Key Setup Script for RichesReach Deployment
# This script helps you add your SSH key to the server
echo " Setting up SSH key for server access..."
# Your SSH public key
SSH_PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJJQyngG4dJB3LyZnQYJcQ+qyeT0I6XsH88VHAX6UC2p marion205@users.noreply.github.com"
echo "Your SSH public key:"
echo "$SSH_PUBLIC_KEY"
echo ""
echo " To add this key to your server, you have two options:"
echo ""
echo "Option 1: If you have password access to the server:"
echo "ssh-copy-id ubuntu@18.217.92.158"
echo ""
echo "Option 2: Manual setup (if you have server console access):"
echo "1. Log into your server console (AWS EC2, DigitalOcean, etc.)"
echo "2. Run these commands on the server:"
echo " mkdir -p ~/.ssh"
echo " echo '$SSH_PUBLIC_KEY' >> ~/.ssh/authorized_keys"
echo " chmod 700 ~/.ssh"
echo " chmod 600 ~/.ssh/authorized_keys"
echo ""
echo "Option 3: Use AWS EC2 key pair (if using AWS):"
echo "1. Download your EC2 key pair (.pem file)"
echo "2. Run: ssh -i your-key.pem ubuntu@18.217.92.158"
echo "3. Then add the SSH key manually"
echo ""
read -p "Press Enter when you've set up SSH access, then we'll continue with deployment..."
echo " Testing SSH connection..."
if ssh -o ConnectTimeout=10 ubuntu@18.217.92.158 "echo 'SSH connection successful'"; then
echo " SSH connection successful! Proceeding with deployment..."
echo ""
echo " Now running the deployment..."
./scripts/quick_deploy.sh
else
echo " SSH connection still failing. Please check your setup and try again."
echo ""
echo "Common issues:"
echo "1. Make sure the SSH key is added to ~/.ssh/authorized_keys on the server"
echo "2. Check that the server allows SSH key authentication"
echo "3. Verify the server IP and username are correct"
echo "4. Make sure your security group allows SSH (port 22) access"
fi
