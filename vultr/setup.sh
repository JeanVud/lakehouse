apt-get update
apt-get install -y git

# INSTALL DOCKER
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# INSTALL DOCKER-COMPOSE
sudo apt-get install -y docker-compose

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install -y  docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin


# INSTALL SNAP
sudo apt-get install -y snapd

# INSTALL CERTBOT
# https://certbot.eff.org/instructions?ws=nginx&os=snap
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable # if firewall is not enabled
sudo ufw status

sudo certbot certonly --standalone -d quynhgiang.info