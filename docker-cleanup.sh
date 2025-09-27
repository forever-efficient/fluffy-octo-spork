#!/bin/bash
# Complete Docker Removal Script for Proxmox
# This will remove ALL Docker containers, images, volumes, networks, and the Docker installation

set -e

echo "=========================================="
echo "COMPLETE DOCKER REMOVAL AND CLEANUP"
echo "=========================================="
echo "WARNING: This will remove ALL Docker data!"
echo "Press Ctrl+C within 10 seconds to cancel..."
sleep 10

echo "Starting Docker cleanup..."

# Step 1: Stop all running containers
echo "1. Stopping all running Docker containers..."
if command -v docker &> /dev/null; then
    # Stop all running containers
    docker stop $(docker ps -aq) 2>/dev/null || echo "No running containers to stop"
    
    # Remove all containers
    echo "2. Removing all Docker containers..."
    docker rm $(docker ps -aq) 2>/dev/null || echo "No containers to remove"
    
    # Remove all images
    echo "3. Removing all Docker images..."
    docker rmi $(docker images -q) -f 2>/dev/null || echo "No images to remove"
    
    # Remove all volumes
    echo "4. Removing all Docker volumes..."
    docker volume prune -f 2>/dev/null || echo "No volumes to prune"
    docker volume rm $(docker volume ls -q) 2>/dev/null || echo "No volumes to remove"
    
    # Remove all networks
    echo "5. Removing all Docker networks..."
    docker network prune -f 2>/dev/null || echo "No networks to prune"
    
    # System prune to clean up everything
    echo "6. Running Docker system prune..."
    docker system prune -af --volumes 2>/dev/null || echo "System prune completed"
else
    echo "Docker command not found, skipping container cleanup"
fi

# Step 2: Stop Docker services
echo "7. Stopping Docker services..."
systemctl stop docker.socket 2>/dev/null || echo "Docker socket not running"
systemctl stop docker 2>/dev/null || echo "Docker service not running"
systemctl stop containerd 2>/dev/null || echo "Containerd not running"

# Step 3: Remove Docker packages
echo "8. Removing Docker packages..."
# For Debian/Ubuntu systems (Proxmox is Debian-based)
apt-get remove -y docker docker-engine docker.io containerd runc docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>/dev/null || echo "Some Docker packages were not installed"

# Purge packages and their configuration files
apt-get purge -y docker docker-engine docker.io containerd runc docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>/dev/null || echo "Purge completed"

# Step 4: Remove Docker directories and files
echo "9. Removing Docker directories and files..."

# Main Docker directory
rm -rf /var/lib/docker
rm -rf /var/lib/containerd

# Docker configuration
rm -rf /etc/docker
rm -rf /etc/containerd

# Docker logs
rm -rf /var/log/docker.log
rm -rf /var/log/docker

# Docker systemd files
rm -f /etc/systemd/system/docker.service
rm -f /etc/systemd/system/docker.socket
rm -f /lib/systemd/system/docker.service
rm -f /lib/systemd/system/docker.socket
rm -f /lib/systemd/system/containerd.service

# Docker group
groupdel docker 2>/dev/null || echo "Docker group already removed or doesn't exist"

# Step 5: Remove Docker Compose
echo "10. Removing Docker Compose..."
rm -f /usr/local/bin/docker-compose
rm -f /usr/bin/docker-compose

# Step 6: Remove any Docker-related cron jobs
echo "11. Checking for Docker-related cron jobs..."
crontab -l 2>/dev/null | grep -v docker | crontab - 2>/dev/null || echo "No Docker cron jobs found"

# Step 7: Clean up any remaining Docker processes
echo "12. Killing any remaining Docker processes..."
pkill -f docker 2>/dev/null || echo "No Docker processes running"
pkill -f containerd 2>/dev/null || echo "No containerd processes running"

# Step 8: Remove Docker repository and keys
echo "13. Removing Docker repository and keys..."
rm -f /etc/apt/sources.list.d/docker.list
rm -f /etc/apt/keyrings/docker.gpg
rm -f /usr/share/keyrings/docker-archive-keyring.gpg

# Step 9: Clean up any leftover network interfaces
echo "14. Cleaning up Docker network interfaces..."
ip link show | grep docker | awk '{print $2}' | sed 's/:$//' | while read interface; do
    ip link delete $interface 2>/dev/null || echo "Could not delete interface $interface"
done

# Clean up bridge interfaces
ip link show | grep br- | awk '{print $2}' | sed 's/:$//' | while read bridge; do
    ip link delete $bridge 2>/dev/null || echo "Could not delete bridge $bridge"
done

# Step 10: Remove any Docker-related mount points
echo "15. Unmounting any Docker-related filesystems..."
mount | grep docker | awk '{print $3}' | while read mountpoint; do
    umount $mountpoint 2>/dev/null || echo "Could not unmount $mountpoint"
done

# Step 11: Clean up iptables rules
echo "16. Flushing Docker iptables rules..."
# Save current iptables rules
iptables-save > /tmp/iptables-backup-$(date +%Y%m%d-%H%M%S)

# Remove Docker chains
iptables -t nat -F DOCKER 2>/dev/null || echo "No DOCKER nat chain"
iptables -t nat -X DOCKER 2>/dev/null || echo "No DOCKER nat chain to delete"
iptables -t filter -F DOCKER 2>/dev/null || echo "No DOCKER filter chain"
iptables -t filter -X DOCKER 2>/dev/null || echo "No DOCKER filter chain to delete"
iptables -t filter -F DOCKER-ISOLATION-STAGE-1 2>/dev/null || echo "No DOCKER-ISOLATION-STAGE-1 chain"
iptables -t filter -X DOCKER-ISOLATION-STAGE-1 2>/dev/null || echo "No DOCKER-ISOLATION-STAGE-1 chain to delete"
iptables -t filter -F DOCKER-ISOLATION-STAGE-2 2>/dev/null || echo "No DOCKER-ISOLATION-STAGE-2 chain"
iptables -t filter -X DOCKER-ISOLATION-STAGE-2 2>/dev/null || echo "No DOCKER-ISOLATION-STAGE-2 chain to delete"
iptables -t filter -F DOCKER-USER 2>/dev/null || echo "No DOCKER-USER chain"
iptables -t filter -X DOCKER-USER 2>/dev/null || echo "No DOCKER-USER chain to delete"

# Step 12: Reload systemd daemon
echo "17. Reloading systemd daemon..."
systemctl daemon-reload

# Step 13: Update package lists
echo "18. Updating package lists..."
apt-get update

# Step 14: Clean up package cache
echo "19. Cleaning up package cache..."
apt-get autoremove -y
apt-get autoclean

# Step 15: Check for any remaining Docker-related files
echo "20. Checking for any remaining Docker files..."
find /var/lib -name "*docker*" -type d 2>/dev/null | head -10
find /etc -name "*docker*" 2>/dev/null | head -10
find /usr -name "*docker*" 2>/dev/null | head -10

echo ""
echo "=========================================="
echo "CLEANUP COMPLETE!"
echo "=========================================="
echo ""
echo "Docker has been completely removed from your system."
echo "You can now proceed with the fresh installation."
echo ""
echo "IMPORTANT: Please reboot your Proxmox host before installing Docker again:"
echo "  reboot"
echo ""
echo "After reboot, you can run the fresh installation script."
echo ""

# Step 16: Create verification script
cat > /tmp/verify-docker-removal.sh << 'EOF'
#!/bin/bash
echo "=========================================="
echo "DOCKER REMOVAL VERIFICATION"
echo "=========================================="

echo "1. Checking for Docker processes..."
if pgrep -f docker > /dev/null; then
    echo "❌ Docker processes still running:"
    pgrep -f docker
else
    echo "✅ No Docker processes running"
fi

echo ""
echo "2. Checking for Docker commands..."
if command -v docker > /dev/null; then
    echo "❌ Docker command still available"
else
    echo "✅ Docker command removed"
fi

echo ""
echo "3. Checking for Docker directories..."
if [ -d "/var/lib/docker" ]; then
    echo "❌ /var/lib/docker still exists"
else
    echo "✅ /var/lib/docker removed"
fi

if [ -d "/etc/docker" ]; then
    echo "❌ /etc/docker still exists"
else
    echo "✅ /etc/docker removed"
fi

echo ""
echo "4. Checking for Docker services..."
if systemctl list-unit-files | grep -q docker; then
    echo "❌ Docker services still registered:"
    systemctl list-unit-files | grep docker
else
    echo "✅ No Docker services registered"
fi

echo ""
echo "5. Checking for Docker networks..."
if ip link show | grep -q docker; then
    echo "❌ Docker network interfaces still exist:"
    ip link show | grep docker
else
    echo "✅ No Docker network interfaces found"
fi

echo ""
echo "6. Checking disk space freed..."
df -h /var/lib
echo ""
echo "Verification complete!"
EOF

chmod +x /tmp/verify-docker-removal.sh

echo "Verification script created at /tmp/verify-docker-removal.sh"
echo "Run it after reboot to verify complete removal."