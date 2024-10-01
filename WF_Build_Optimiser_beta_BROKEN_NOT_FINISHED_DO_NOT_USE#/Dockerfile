# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory
WORKDIR /WF_Build_Optimiser_beta

# Copy requirements.txt and install the dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code to the container
COPY WF_Build_Optimiser_beta.py .

# Expose the port Streamlit uses.
EXPOSE 8501

# Specify the command to run your WF_Build_Optimiser_beta
CMD ["streamlit", "run", "WF_Build_Optimiser_beta.py", "--server.port=8501", "--server.address=0.0.0.0"]