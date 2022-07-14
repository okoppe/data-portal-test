FROM ubuntu:latest
# Update package manager (apt-get)
# and install (with the yes flag `-y`)
# Python and Pip
RUN apt-get update && apt-get install -y \
    python3.8 \
    python3-pip

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt
CMD [ "python3", "-m" , "flask", "run", "--no-reload", "--host=0.0.0.0"]
