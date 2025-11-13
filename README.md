# From notebook to cloud: Deploy ML model on Ubuntu

## About

Through this workshop, you will gain hands-on experience in the MLOps workflow by using Podman for containerization and Microk8s for Deployment.

## System requirements

- 8 GB RAM [16 GB better]
- Atleast 40GB free space on disk

## Prerequisites

- Ubuntu LTS
- Python3
```
sudo apt install -y python3
```
- Venv
```
sudo apt install -y python3-venv
```
- Git
```
sudo apt install -y git
``` 
- Curl
```
sudo apt install -y curl
```
- Podman
```
sudo apt install -y podman
```
- Microk8s [go to step E]
```
sudo snap install microk8s --classic
```
- Will to learn

## Folder structure

Workshop_root/<br />
├── app/<br />
│   ├── app.py<br />
│   ├── Containerfile<br />
├── model/<br />
│   ├── model.pkl<br />
│   └── vectorizer.pkl<br />
├── dataset/<br />
│   └── dataset.csv<br />
├── notebook/<br />
│   └── mlops.ipynb<br />
├── k8s/<br />
│   ├── deployment.yaml<br />
│   ├── service.yaml<br />
│   └── ingress.yaml<br />
├── README.md<br />
└── requirements.txt<br />
└── <venv_name>

## Steps to follow:

### A. Virtual environment

- Create a virtual environment(venv)
```
python3 -m venv <venv_name>
```
- Activate the venv
```
source <venv_name>/bin/activate
```
- Install the required packages within venv
```
pip install -r requirements.txt
```
- Add the kernel to notebook
```
python3 -m ipykernel install --user --name=<venv_name> --display-name "Py(<venv_name>)"
```
- Exit the venv
```
deactivate
```


### B. Dataset

- Follow the link to [download the dataset](https://www.kaggle.com/datasets/mexwell/telegram-spam-or-ham)


### C. Notebook

- Install notebook outside virtual environment
```
sudo apt install -y python3-notebook
```
- Open jupyter notebook
```
jupyter notebook
```
- Change kernel to your virtual environment
- Import the libraraies and then download the nltk files
- Run the cells
- Save the model and vectorizer to model folder for future use.
- Save and checkpoint the notebook


### D. Containerization

- In /app folder, create a file app.py
```python
from fastapi import FastAPI
from pydantic import BaseModel
import joblib

app = FastAPI()

# Load model and vectorizer
model = joblib.load("model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

class TextInput(BaseModel):
    msg: str

@app.post("/predict")
def predict(data: TextInput):
    text = data.msg
    text_vector = vectorizer.transform([text])
    prediction = model.predict(text_vector)
    result = prediction[0]
    return {"sentiment": str(result)}
```

- Create the Containerfile
```
#Lightweight Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

#Copy dependency list and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#copy the app code
COPY app/app.py .

#Copy the model file
COPY model/model.pkl .
COPY model/vectorizer.pkl .

#Expose the FastAPI port
EXPOSE 8000

#Run the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

- Build the image
```
podman build -t spam-ham -f app/Containerfile .
```
- Run the container
```
podman run -d -p 8000:8000 spam-ham
```
- Check if all the files are present in the container shell
```
podman run -it spam-ham/bin/bash
```
```
/app#
```
```
exit
```
- On your browser, visit localhost:8000/docs
![Image](https://github.com/user-attachments/assets/67cf25d7-08b3-46ac-b886-b3c17e0f5a5a) <br />
![Image](https://github.com/user-attachments/assets/f401bb69-21c4-4a6f-b27d-c8e6eb54729d) <br />
![Image](https://github.com/user-attachments/assets/425d0b91-9014-4a3c-aa53-175f397d8e84) <br />
![Image](https://github.com/user-attachments/assets/071efd2d-44ce-4cb1-b873-d00427596f07) <br />
- Click on Try it out, edit the msg field and execute.


### E. Setting Microk8s

- Install MicroK8s
```
sudo snap install microk8s --classic --channel=1.30/stable
```
- Add current user to MicroK8s group
```
sudo usermod -a -G microk8s $USER
```
- Apply group change without reboot
```
newgrp microk8s
```
- Check status
```
microk8s status --wait-ready
```
- Enable Kubernetes essentials
```
microk8s enable dns registry ingress
```


### F. Configure Podman to Use an Insecure Local Registry
- Create your personal registries configuration file
```
mkdir -p ~/.config/containers
```
```
nano ~/.config/containers/registries.conf
```
- Edit the configuration file to add an insecure registry 
```
[registries.search]
registries = ['docker.io']
[registries.insecure]
registries = ['localhost:32000']
[registries.block]
registries = []
```
- Save the file (Ctrl + O, then Enter)
- Close the file (Ctrl + X).
- Restart the Podman socket
```
systemctl --user restart podman.socket 2>/dev/null || true
```
- Verify your configuration loaded correctly
```
podman info | grep -A3 registries
```
- You should see something like:
```
registries:
  localhost:32000:
    Blocked: false
    Insecure: true
```


### G. Deployment

- Add the deployment definition => **deployment.yaml**
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spam-ham
spec:
  replicas: 1
  selector:
    matchLabels:
      app: spam-ham
  template:
    metadata:
      labels:
        app: spam-ham
    spec:
      containers:
      - name: spam-ham
        image: localhost:32000/spam-ham:latest
        ports:
        - containerPort: 8000
```
- Add the service exposure => **service.yaml**
```
apiVersion: v1
kind: Service
metadata:
  name: spamham-service
spec:
  selector:
    app: spam-ham
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: NodePort
```
- Add the ingress file  => ingress.yaml
```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: spamham-ingress
spec:
  rules:
  - host: spam.ham 
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: spamham-service
            port:
              number: 80
```
- Tag your Podman image for MicroK8s local registry
```
podman tag spam-ham localhost:32000/spam-ham:latest
```
- Push to MicroK8s registry
```
podman push localhost:32000/spam-ham:latest
```
- Apply to Cluster
```
cd k8s
```
```
microk8s kubectl apply -f deployment.yaml
```
```
microk8s kubectl apply -f service.yaml
```
```
microk8s kubectl apply -f ingress.yaml
```
```
echo "127.0.0.1 spam.ham" | sudo tee -a /etc/hosts
```


### H. Testing the endpoint

- Test a case from terminal:
  - where the output is spam
```
curl http://spam.ham/predict \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"msg": "Unbelievable offer! Buy 1 get 4 free, click on this link to claim"}'
```
![Image](https://github.com/user-attachments/assets/4f57ff32-6b14-484e-886e-eb426456d070)
  - where the output is ham
```
curl http://spam.ham/predict \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"msg": "I am attending Ubucon India 2025!"}'
```
![Image](https://github.com/user-attachments/assets/cee8e612-4b1c-495a-9a9c-55f9d3de211b)
- Test a case from browser
https://spam.ham/docs
![Image](https://github.com/user-attachments/assets/b18ac90a-680b-4324-8432-a444976a7473)

## Contact

Have any doubts? Reach out to us: <br />
- [Saumili Dutta](https://www.linkedin.com/in/saumilidutta/)<br />
- [Aditya D.](https://www.linkedin.com/in/aditya-d-23453a179/)<br />

Access our ppt [here](https://www.canva.com/design/DAG4kZ4QsnA/MIdBMDJ1Ru_S1z7expmhkQ/edit)
