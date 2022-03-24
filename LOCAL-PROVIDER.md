# Installation on EC2

## install zsh
```bash
sudo apt-get update && sudo apt-get install -y curl vim git zsh
curl -L https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh | bash
sudo chsh -s $(which zsh) $(whoami)
```

## install ubuntu desktop on ec2

```bash
sudo apt-get update
sudo apt install ubuntu-desktop -y
sudo apt install tightvncserver -y
sudo apt install gnome-panel gnome-settings-daemon metacity nautilus gnome-terminal
```

```
#➜  ~ vncserver
#
#You will require a password to access your desktops.
#
#Password:
#Verify:
#Would you like to enter a view-only password (y/n)? y
#Password:
#Verify:
#xauth:  file /home/ubuntu/.Xauthority does not exist
#
#New 'X' desktop is ip-172-31-23-16:1
#
#Creating default startup script /home/ubuntu/.vnc/xstartup
#Starting applications specified in /home/ubuntu/.vnc/xstartup
#Log file is /home/ubuntu/.vnc/ip-172-31-23-16:1.log
```

```bash

sudo apt-get install lxde -y
sudo apt-get install xrdp -y

sudo passwd ubuntu
```


## Set up User data on EC2

```bash
#!/bin/bash
echo ubuntu:hardc0re | sudo chpasswd
```


## Ubuntu startup script

path: `~/.config/autostart/local-provider.desktop`

```
[Desktop Entry]
Type=Application
Exec=gnome-terminal --working-directory=/home/ubuntu/dev/ep-sc/local/ -- sh local-provider.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name[C]=local-provider
Name=local-provider
Comment[C]=
Comment=
```

## Ubuntu startup script for docker-compose

path: `/etc/systemd/system/ep-sc.service`

```
[Unit]
Description=ep-sc service with docker compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStartPre=/usr/local/bin/docker-compose --env-file .env pull
ExecStart=/usr/local/bin/docker-compose --env-file .env up -d
ExecStop=/usr/local/bin/docker-compose down

[Install]
WantedBy=multi-user.target

```

