FROM python:3.9-slim-buster

COPY . /purplepanda

RUN apt update; apt install -y wget

# install gcloud
RUN apt-get install -y apt-transport-https ca-certificates gnupg curl; \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list; \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -; \
    apt-get update && apt-get install -y google-cloud-cli

# Install gitleaks
RUN mkdir /tmp/gl
RUN wget https://github.com/zricethezav/gitleaks/releases/download/v8.8.4/gitleaks_8.8.4_linux_x64.tar.gz -P /tmp/gl
RUN cd /tmp/gl; tar -xvzf gitleaks_8.8.4_linux_x64.tar.gz
RUN chmod +x /tmp/gl/gitleaks
RUN mv /tmp/gl/gitleaks /usr/local/bin/gitleaks

# Install purplepanda
RUN cd /purplepanda; python3 -m pip install -r requirements.txt

WORKDIR /purplepanda

# You can set the env variables here if you need it
#ENV PURPLEPANDA_NEO4J_URL=...
#ENV PURPLEPANDA_PWD=...
#ENV GOOGLE_DISCOVERY=...
#ENV GITHUB_DISCOVERY=...
#ENV K8S_DISCOVERY=...
#ENV CONCOURSE_DISCOVERY=...
#ENV CIRCLECI_DISCOVERY=...

CMD /usr/bin/python3 main.py