# Base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy files
COPY app.py /app
COPY requirements.txt /app
COPY utils /app/utils

# Install dependencies
RUN pip install -r requirements.txt

# Run the application
EXPOSE 8000
#EXPOSE 8501 

#ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "--timeout", "120"]
#CMD ["app:app"]


#RUN apt-get update && apt-get install -y \
#    build-essential \
#    software-properties-common \
#    git \
#    && rm -rf /var/lib/apt/lists/*

#RUN git clone https://github.com/streamlit/streamlit-example.git .

#RUN pip3 install -r requirements.txt

#ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]