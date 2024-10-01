#!/bin/bash

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install necessary packages
sudo apt install -y python3.12 python3.12-venv nginx

# Create a directory for the application
sudo mkdir -p /opt/warframe-optimizer
sudo chown $USER:$USER /opt/warframe-optimizer

# Navigate to the application directory
cd /opt/warframe-optimizer

# Create a virtual environment
python3.12 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Create the main Python file (assuming your file is named 'WF_Build_Optimiser_Charlie.py')
cp WF_Build_Optimiser_Charlie.py . 

# Create requirements.txt
cat > requirements.txt << EOL
streamlit==1.10.0
pandas==1.3.5
matplotlib==3.5.2
numpy==1.21.6
sqlalchemy==1.4.39
requests==2.28.1
lxml==4.9.1
EOL

# Install Python dependencies
pip install -r requirements.txt

# Create a systemd service file
sudo tee /etc/systemd/system/warframe-optimizer.service > /dev/null << EOL
[Unit]
Description=Warframe Build Optimizer Streamlit App
After=network.target

[Service]
User=$USER
WorkingDirectory=/opt/warframe-optimizer
ExecStart=/opt/warframe-optimizer/venv/bin/streamlit run WF_Build_Optimiser_Charlie.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Enable and start the service
sudo systemctl enable warframe-optimizer
sudo systemctl start warframe-optimizer

# Configure Nginx as a reverse proxy
sudo tee /etc/nginx/sites-available/warframe-optimizer > /dev/null << EOL
server {
    listen 80;
    server_name your_domain.com;  # Replace with your actual domain

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOL

# Enable the Nginx site
sudo ln -s /etc/nginx/sites-available/warframe-optimizer /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# If the test is successful, reload Nginx
if [ $? -eq 0 ]; then
    sudo systemctl reload nginx
else
    echo "Nginx configuration test failed. Please check the configuration."
fi

echo "Deployment complete. Your Warframe Build Optimizer should now be accessible at http://your_domain.com" 