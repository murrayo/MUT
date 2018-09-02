# Use official Python 3.6 from docker hub
# So you know you are running the same version
FROM python:3.6

# Change to root of container
WORKDIR .

# Needed packages list built using pipreqs
COPY requirements.txt ./

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts into container
COPY . .